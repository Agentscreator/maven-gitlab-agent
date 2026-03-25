"""Integrates GitLab webhooks with the Maven runtime.

Bridges the gap between the generic WebhookServer (which publishes raw
WEBHOOK_RECEIVED events) and the GitLab-specific event router (which
produces MavenGoals). Subscribes to the EventBus and feeds parsed
GitLab events into the Queen agent.

Also provides a standalone aiohttp route handler for the server app,
so GitLab webhooks can be received through the main HTTP server
(port 8787) without needing a separate webhook server.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from framework.gitlab.config import GitLabConfig, get_gitlab_config
from framework.gitlab.event_router import GitLabEventRouter, MavenGoal
from framework.gitlab.webhook_handler import (
    GitLabWebhookEvent,
    parse_gitlab_event,
    verify_gitlab_token,
)
from framework.runtime.event_bus import AgentEvent, EventBus, EventType

logger = logging.getLogger(__name__)


class GitLabWebhookIntegration:
    """Connects GitLab webhooks to the Maven event system.

    Two modes of operation:
    1. Standalone: subscribes to WEBHOOK_RECEIVED events on the EventBus
       (when using the dedicated WebhookServer on a separate port).
    2. Server route: provides an aiohttp handler that can be mounted
       on the main server app (preferred for simplicity).
    """

    def __init__(
        self,
        event_bus: EventBus,
        config: GitLabConfig | None = None,
        on_goal: Any | None = None,
    ):
        """
        Args:
            event_bus: The runtime event bus.
            config: GitLab config (auto-loaded if None).
            on_goal: Optional async callback(MavenGoal) for custom handling.
        """
        self._event_bus = event_bus
        self._config = config or get_gitlab_config()
        self._router = GitLabEventRouter()
        self._on_goal = on_goal
        self._subscription_id: str | None = None

    def subscribe_to_event_bus(self) -> None:
        """Subscribe to WEBHOOK_RECEIVED events from the generic WebhookServer."""
        if self._subscription_id:
            return

        async def _handle_webhook_event(event: AgentEvent) -> None:
            # Only handle events from our gitlab webhook source
            if event.stream_id != "gitlab":
                return
            headers = event.data.get("headers", {})
            payload = event.data.get("payload", {})
            await self._process_webhook(headers, payload)

        self._subscription_id = self._event_bus.subscribe(
            event_types=[EventType.WEBHOOK_RECEIVED],
            handler=_handle_webhook_event,
        )
        logger.info("GitLab webhook integration subscribed to EventBus.")

    def unsubscribe(self) -> None:
        if self._subscription_id:
            self._event_bus.unsubscribe(self._subscription_id)
            self._subscription_id = None

    async def _process_webhook(
        self,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> MavenGoal | None:
        """Parse, verify, route, and publish a GitLab webhook event."""
        # Verify token
        request_token = headers.get("X-Gitlab-Token")
        if not verify_gitlab_token(request_token, self._config):
            logger.warning("GitLab webhook rejected: invalid token")
            return None

        # Parse event
        event = parse_gitlab_event(headers, payload)
        logger.info(
            "GitLab event: %s (project=%s)",
            event.event_key,
            event.project_path,
        )

        # Publish raw GitLab event to bus for observability
        await self._event_bus.publish(
            AgentEvent(
                type=EventType.CUSTOM,
                stream_id="gitlab",
                data={
                    "custom_type": "gitlab_event",
                    "event_key": event.event_key,
                    "project_path": event.project_path,
                    "payload_summary": _summarize_payload(event),
                },
            )
        )

        # Route to a Maven goal
        goal = self._router.route(event)
        if goal is None:
            logger.debug("Event %s produced no goal — skipping.", event.event_key)
            return None

        # Publish goal as a custom event so the Queen can pick it up
        await self._event_bus.publish(
            AgentEvent(
                type=EventType.CUSTOM,
                stream_id="gitlab",
                data={
                    "custom_type": "maven_goal",
                    "goal_type": goal.goal_type,
                    "priority": goal.priority,
                    "summary": goal.summary,
                    "context": goal.context,
                    "suggested_workers": goal.suggested_workers,
                    "requires_human_approval": goal.requires_human_approval,
                    "source_event": goal.source_event,
                },
            )
        )

        # Custom callback if provided
        if self._on_goal:
            try:
                await self._on_goal(goal)
            except Exception:
                logger.error("on_goal callback failed", exc_info=True)

        return goal

    # ------------------------------------------------------------------
    # aiohttp route handler (for mounting on the main server)
    # ------------------------------------------------------------------

    async def handle_webhook_request(self, request: web.Request) -> web.Response:
        """aiohttp handler for POST /webhooks/gitlab.

        Mount this on the main server app so GitLab can send webhooks
        to the same port as the dashboard.
        """
        try:
            body = await request.read()
        except Exception:
            return web.json_response({"error": "Failed to read body"}, status=400)

        try:
            payload = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            return web.json_response({"error": "Invalid JSON"}, status=400)

        headers = dict(request.headers)
        goal = await self._process_webhook(headers, payload)

        if goal:
            return web.json_response(
                {"status": "accepted", "goal": goal.goal_type},
                status=202,
            )
        # Still return 200 even if no goal — GitLab expects 2xx
        return web.json_response({"status": "ok", "goal": None}, status=200)


def _summarize_payload(event: GitLabWebhookEvent) -> dict[str, Any]:
    """Create a compact summary of the event for logging/observability."""
    summary: dict[str, Any] = {
        "event_type": event.event_type,
        "action": event.action,
        "project": event.project_path,
    }
    attrs = event.payload.get("object_attributes", {})
    if attrs.get("title"):
        summary["title"] = attrs["title"][:100]
    if attrs.get("iid"):
        summary["iid"] = attrs["iid"]
    if attrs.get("status"):
        summary["status"] = attrs["status"]
    return summary


def register_gitlab_webhook_routes(app: web.Application, event_bus: EventBus) -> None:
    """Register GitLab webhook routes on the aiohttp app.

    Called from create_app() — only sets up routes if GitLab is configured.
    Gracefully no-ops if GitLab is not configured.
    """
    from framework.gitlab.config import is_gitlab_configured

    if not is_gitlab_configured():
        logger.debug("GitLab not configured — webhook routes not registered.")
        return

    config = get_gitlab_config()
    integration = GitLabWebhookIntegration(event_bus, config)

    # Mount the webhook endpoint
    path = config.webhook_path
    app.router.add_post(path, integration.handle_webhook_request)
    logger.info("GitLab webhook route registered: POST %s", path)

    # Store integration on app for access by other components
    app["gitlab_integration"] = integration
