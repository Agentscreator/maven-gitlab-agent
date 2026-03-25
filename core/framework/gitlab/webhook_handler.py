"""GitLab webhook handler — parses incoming events and publishes to EventBus.

GitLab sends a different header layout than GitHub:
- X-Gitlab-Token: shared secret (not HMAC — just a plain token comparison)
- X-Gitlab-Event: event type string (e.g. "Push Hook", "Merge Request Hook")

This module plugs into the existing WebhookServer infrastructure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from framework.gitlab.config import GitLabConfig, get_gitlab_config

logger = logging.getLogger(__name__)


# Maps X-Gitlab-Event header values to internal event categories
GITLAB_EVENT_MAP: dict[str, str] = {
    "Push Hook": "push",
    "Tag Push Hook": "tag_push",
    "Issue Hook": "issue",
    "Note Hook": "note",
    "Merge Request Hook": "merge_request",
    "Wiki Page Hook": "wiki_page",
    "Pipeline Hook": "pipeline",
    "Job Hook": "job",
    "Deployment Hook": "deployment",
    "Feature Flag Hook": "feature_flag",
    "Release Hook": "release",
    "Emoji Hook": "emoji",
    "Confidential Issue Hook": "issue",
    "Confidential Note Hook": "note",
}


@dataclass
class GitLabWebhookEvent:
    """Parsed GitLab webhook event."""

    event_type: str  # Internal category (push, issue, merge_request, etc.)
    gitlab_event: str  # Raw X-Gitlab-Event header value
    action: str | None  # Sub-action (opened, closed, merged, etc.)
    project_id: int | None
    project_path: str | None
    payload: dict[str, Any]

    @property
    def event_key(self) -> str:
        """Unique key like 'merge_request.opened' or 'pipeline.failed'."""
        if self.action:
            return f"{self.event_type}.{self.action}"
        return self.event_type


def verify_gitlab_token(
    request_token: str | None,
    config: GitLabConfig | None = None,
) -> bool:
    """Verify the X-Gitlab-Token header matches our configured secret.

    GitLab uses a simple shared-secret comparison (not HMAC).
    Returns True if no secret is configured (open mode).
    """
    cfg = config or get_gitlab_config()
    if not cfg.webhook_secret:
        # No secret configured — accept all (useful for local dev)
        return True
    if not request_token:
        return False
    # Constant-time comparison to prevent timing attacks
    import hmac

    return hmac.compare_digest(request_token, cfg.webhook_secret)


def parse_gitlab_event(
    headers: dict[str, str],
    payload: dict[str, Any],
) -> GitLabWebhookEvent:
    """Parse a raw webhook request into a structured GitLabWebhookEvent."""
    gitlab_event_header = headers.get("X-Gitlab-Event", "")
    event_type = GITLAB_EVENT_MAP.get(gitlab_event_header, "unknown")

    # Extract action from payload (varies by event type)
    action = _extract_action(event_type, payload)

    # Extract project info
    project = payload.get("project", {})
    project_id = project.get("id")
    project_path = project.get("path_with_namespace")

    return GitLabWebhookEvent(
        event_type=event_type,
        gitlab_event=gitlab_event_header,
        action=action,
        project_id=project_id,
        project_path=project_path,
        payload=payload,
    )


def _extract_action(event_type: str, payload: dict[str, Any]) -> str | None:
    """Extract the sub-action from a GitLab webhook payload."""
    if event_type == "merge_request":
        attrs = payload.get("object_attributes", {})
        return attrs.get("action")  # opened, closed, merged, updated, etc.

    if event_type == "issue":
        attrs = payload.get("object_attributes", {})
        return attrs.get("action")  # open, close, reopen, update

    if event_type == "pipeline":
        attrs = payload.get("object_attributes", {})
        status = attrs.get("status")  # success, failed, running, pending
        return status

    if event_type == "job":
        status = payload.get("build_status")  # success, failed, etc.
        return status

    if event_type == "note":
        # Comments — action is the noteable_type (Issue, MergeRequest, etc.)
        attrs = payload.get("object_attributes", {})
        return attrs.get("noteable_type", "").lower()

    if event_type == "push":
        return None  # Push events don't have sub-actions

    return None
