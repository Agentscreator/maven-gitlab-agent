"""GitLab event router — maps webhook events to Maven agent goals.

This is the brain that decides what Maven should do when a GitLab event
arrives. It translates raw webhook events into structured goals that the
Queen agent can interpret and delegate to worker castes.

The router is intentionally decoupled from the Queen — it produces goal
descriptions that any orchestrator can consume.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from framework.gitlab.webhook_handler import GitLabWebhookEvent

logger = logging.getLogger(__name__)


@dataclass
class MavenGoal:
    """A goal for the Maven swarm to pursue."""

    goal_type: str  # security_fix, pipeline_recovery, triage, etc.
    priority: str  # critical, high, medium, low
    summary: str  # Human-readable one-liner
    context: dict[str, Any]  # Structured data for the worker
    suggested_workers: list[str]  # Worker castes to involve
    requires_human_approval: bool = False
    source_event: str = ""  # The event_key that triggered this goal
    metadata: dict[str, Any] = field(default_factory=dict)


class GitLabEventRouter:
    """Routes GitLab webhook events to Maven goals.

    Each handler method returns a MavenGoal (or None to skip the event).
    The Queen agent receives these goals and generates worker graphs.
    """

    def route(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        """Route a GitLab event to a Maven goal."""
        handler = self._handlers.get(event.event_type)
        if handler is None:
            logger.debug("No handler for event type: %s", event.event_type)
            return None

        try:
            goal = handler(self, event)
            if goal:
                goal.source_event = event.event_key
                logger.info(
                    "Routed %s → %s (priority=%s)",
                    event.event_key,
                    goal.goal_type,
                    goal.priority,
                )
            return goal
        except Exception:
            logger.error("Error routing event %s", event.event_key, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_pipeline(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        attrs = event.payload.get("object_attributes", {})
        status = attrs.get("status")

        if status == "failed":
            return MavenGoal(
                goal_type="pipeline_recovery",
                priority="high",
                summary=f"Pipeline #{attrs.get('id')} failed — diagnose and fix",
                context={
                    "pipeline_id": attrs.get("id"),
                    "ref": attrs.get("ref"),
                    "source": attrs.get("source"),
                    "failure_reason": attrs.get("failure_reason"),
                    "stages": attrs.get("stages", []),
                    "project_id": event.project_id,
                    "project_path": event.project_path,
                },
                suggested_workers=["deploy"],
            )
        # Ignore success/running/pending — no action needed
        return None

    def _handle_job(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        status = event.payload.get("build_status")
        if status != "failed":
            return None

        return MavenGoal(
            goal_type="job_failure",
            priority="medium",
            summary=f"Job '{event.payload.get('build_name')}' failed",
            context={
                "job_id": event.payload.get("build_id"),
                "job_name": event.payload.get("build_name"),
                "stage": event.payload.get("build_stage"),
                "failure_reason": event.payload.get("build_failure_reason"),
                "pipeline_id": event.payload.get("pipeline_id"),
                "project_id": event.project_id,
                "project_path": event.project_path,
            },
            suggested_workers=["deploy"],
        )

    def _handle_merge_request(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        attrs = event.payload.get("object_attributes", {})
        action = attrs.get("action")

        if action == "open":
            return MavenGoal(
                goal_type="mr_review",
                priority="medium",
                summary=f"MR !{attrs.get('iid')}: {attrs.get('title', '')}",
                context={
                    "mr_iid": attrs.get("iid"),
                    "title": attrs.get("title"),
                    "description": (attrs.get("description") or "")[:2000],
                    "source_branch": attrs.get("source_branch"),
                    "target_branch": attrs.get("target_branch"),
                    "author": (event.payload.get("user") or {}).get("username"),
                    "project_id": event.project_id,
                    "project_path": event.project_path,
                },
                suggested_workers=["compliance", "test"],
            )

        if action == "merge":
            # Post-merge — could trigger deployment checks
            return MavenGoal(
                goal_type="post_merge",
                priority="low",
                summary=f"MR !{attrs.get('iid')} merged into {attrs.get('target_branch')}",
                context={
                    "mr_iid": attrs.get("iid"),
                    "target_branch": attrs.get("target_branch"),
                    "project_id": event.project_id,
                    "project_path": event.project_path,
                },
                suggested_workers=["deploy"],
            )

        return None

    def _handle_issue(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        attrs = event.payload.get("object_attributes", {})
        action = attrs.get("action")

        if action in ("open", "reopen"):
            return MavenGoal(
                goal_type="issue_triage",
                priority="medium",
                summary=f"Issue #{attrs.get('iid')}: {attrs.get('title', '')}",
                context={
                    "issue_iid": attrs.get("iid"),
                    "title": attrs.get("title"),
                    "description": (attrs.get("description") or "")[:2000],
                    "labels": attrs.get("labels", []),
                    "author": (event.payload.get("user") or {}).get("username"),
                    "project_id": event.project_id,
                    "project_path": event.project_path,
                },
                suggested_workers=["triage"],
            )

        return None

    def _handle_push(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        # Pushes are informational — we react to pipeline results instead.
        # But we can use them for security scanning triggers.
        commits = event.payload.get("commits", [])
        if not commits:
            return None

        return MavenGoal(
            goal_type="push_scan",
            priority="low",
            summary=f"{len(commits)} commit(s) pushed to {event.payload.get('ref', '')}",
            context={
                "ref": event.payload.get("ref"),
                "commit_count": len(commits),
                "commits": [
                    {
                        "id": c.get("id", "")[:12],
                        "message": (c.get("message") or "")[:200],
                        "author": c.get("author", {}).get("name"),
                    }
                    for c in commits[:10]  # Cap at 10 to avoid huge payloads
                ],
                "project_id": event.project_id,
                "project_path": event.project_path,
            },
            suggested_workers=["security"],
        )

    def _handle_note(self, event: GitLabWebhookEvent) -> MavenGoal | None:
        # Comments — only act on explicit @maven mentions
        attrs = event.payload.get("object_attributes", {})
        note_body = attrs.get("note", "")
        if "@maven" not in note_body.lower():
            return None

        return MavenGoal(
            goal_type="mention_response",
            priority="medium",
            summary="Maven was mentioned in a comment",
            context={
                "note": note_body[:2000],
                "noteable_type": attrs.get("noteable_type"),
                "noteable_id": attrs.get("noteable_id"),
                "author": (event.payload.get("user") or {}).get("username"),
                "project_id": event.project_id,
                "project_path": event.project_path,
            },
            suggested_workers=["triage"],
        )

    # Handler dispatch table
    _handlers: dict[str, Any] = {
        "pipeline": _handle_pipeline,
        "job": _handle_job,
        "merge_request": _handle_merge_request,
        "issue": _handle_issue,
        "push": _handle_push,
        "note": _handle_note,
    }
