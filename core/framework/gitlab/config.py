"""GitLab configuration management.

Reads GitLab settings from ~/.hive/configuration.json under the "gitlab" key.
Falls back to environment variables (GITLAB_TOKEN, GITLAB_URL, etc.).
All functions return sensible defaults when GitLab is not configured,
so the rest of Maven continues to work without it.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from framework.config import get_hive_config

logger = logging.getLogger(__name__)

DEFAULT_GITLAB_URL = "https://gitlab.com"
DEFAULT_WEBHOOK_PATH = "/webhooks/gitlab"
DEFAULT_WEBHOOK_PORT = 8080

DEFAULT_ENABLED_EVENTS = [
    "push_events",
    "merge_requests_events",
    "issues_events",
    "pipeline_events",
    "job_events",
]


@dataclass
class GitLabConfig:
    """Resolved GitLab configuration."""

    url: str = DEFAULT_GITLAB_URL
    token: str | None = None
    webhook_secret: str | None = None
    webhook_path: str = DEFAULT_WEBHOOK_PATH
    webhook_port: int = DEFAULT_WEBHOOK_PORT
    # Project to monitor (namespace/project format)
    project: str | None = None
    # Which event categories to subscribe to
    enabled_events: list[str] = field(default_factory=lambda: list(DEFAULT_ENABLED_EVENTS))

    @property
    def is_configured(self) -> bool:
        """True if we have enough config to talk to GitLab."""
        return bool(self.token)

    @property
    def api_base(self) -> str:
        """Base URL for GitLab API v4 calls."""
        return f"{self.url.rstrip('/')}/api/v4"


def get_gitlab_config() -> GitLabConfig:
    """Load GitLab configuration from hive config + env vars.

    Priority: env vars override config file values.
    """
    cfg = get_hive_config().get("gitlab", {})

    url = os.environ.get("GITLAB_URL") or cfg.get("url") or DEFAULT_GITLAB_URL
    token = os.environ.get("GITLAB_TOKEN") or cfg.get("token")
    webhook_secret = os.environ.get("GITLAB_WEBHOOK_SECRET") or cfg.get("webhook_secret")
    project = os.environ.get("GITLAB_PROJECT") or cfg.get("project")
    webhook_path = cfg.get("webhook_path", DEFAULT_WEBHOOK_PATH)
    webhook_port = int(cfg.get("webhook_port", DEFAULT_WEBHOOK_PORT))
    enabled_events = cfg.get("enabled_events") or list(DEFAULT_ENABLED_EVENTS)

    return GitLabConfig(
        url=url,
        token=token,
        webhook_secret=webhook_secret,
        webhook_path=webhook_path,
        webhook_port=webhook_port,
        project=project,
        enabled_events=enabled_events,
    )


def is_gitlab_configured() -> bool:
    """Quick check: is GitLab integration available?"""
    return get_gitlab_config().is_configured


def save_gitlab_config(updates: dict[str, Any]) -> None:
    """Persist GitLab settings to ~/.hive/configuration.json.

    Merges *updates* into the existing ``gitlab`` section without
    touching other config keys.
    """
    import json
    from pathlib import Path

    config_path = Path.home() / ".hive" / "configuration.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8-sig") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    gitlab_section = existing.get("gitlab", {})
    gitlab_section.update(updates)
    existing["gitlab"] = gitlab_section

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    logger.info("GitLab config saved to %s", config_path)
