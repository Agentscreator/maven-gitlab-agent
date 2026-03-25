"""GitLab API client for Maven.

Handles webhook registration, project queries, pipeline management,
and merge request operations needed by the autonomous swarm.
Uses httpx for HTTP calls (already a project dependency via the gitlab_tool).
"""

from __future__ import annotations

import logging
import secrets
from typing import Any
from urllib.parse import quote as url_quote

import httpx

from framework.gitlab.config import GitLabConfig, get_gitlab_config, save_gitlab_config

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


class GitLabClientError(Exception):
    """Raised when a GitLab API call fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitLabClient:
    """Thin wrapper around the GitLab REST API v4.

    Designed for the operations Maven needs beyond what the MCP gitlab_tool
    provides (webhook management, pipeline control, file commits, etc.).
    """

    def __init__(self, config: GitLabConfig | None = None):
        self._config = config or get_gitlab_config()
        if not self._config.is_configured:
            raise GitLabClientError(
                "GitLab not configured. Set GITLAB_TOKEN or run 'hive gitlab setup'."
            )

    @property
    def config(self) -> GitLabConfig:
        return self._config

    def _headers(self) -> dict[str, str]:
        return {
            "PRIVATE-TOKEN": self._config.token or "",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._config.api_base}{path}"

    def _encode_project(self, project: str | None = None) -> str:
        """URL-encode a project path (namespace/name → namespace%2Fname)."""
        proj = project or self._config.project
        if not proj:
            raise GitLabClientError("No project specified. Use --project or set gitlab.project.")
        return url_quote(proj, safe="")

    # ------------------------------------------------------------------
    # Low-level HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = httpx.get(
            self._url(path), headers=self._headers(), params=params or {}, timeout=_TIMEOUT
        )
        return self._handle_response(resp)

    def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        resp = httpx.post(
            self._url(path), headers=self._headers(), json=json or {}, timeout=_TIMEOUT
        )
        return self._handle_response(resp)

    def _put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        resp = httpx.put(
            self._url(path), headers=self._headers(), json=json or {}, timeout=_TIMEOUT
        )
        return self._handle_response(resp)

    def _delete(self, path: str) -> Any:
        resp = httpx.delete(self._url(path), headers=self._headers(), timeout=_TIMEOUT)
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: httpx.Response) -> Any:
        if resp.status_code == 401:
            raise GitLabClientError("Unauthorized — check your GitLab token.", 401)
        if resp.status_code == 403:
            raise GitLabClientError("Forbidden — insufficient permissions.", 403)
        if resp.status_code == 404:
            raise GitLabClientError("Not found.", 404)
        if resp.status_code == 429:
            raise GitLabClientError("Rate limited — try again shortly.", 429)
        if resp.status_code not in (200, 201, 204):
            raise GitLabClientError(
                f"GitLab API error {resp.status_code}: {resp.text[:500]}",
                resp.status_code,
            )
        if resp.status_code == 204:
            return {}
        return resp.json()

    # ------------------------------------------------------------------
    # Authentication / health
    # ------------------------------------------------------------------

    def verify_token(self) -> dict[str, Any]:
        """Verify the token works and return the authenticated user."""
        return self._get("/user")

    # ------------------------------------------------------------------
    # Project operations
    # ------------------------------------------------------------------

    def get_project(self, project: str | None = None) -> dict[str, Any]:
        """Get project details."""
        encoded = self._encode_project(project)
        return self._get(f"/projects/{encoded}", {"statistics": "true"})

    # ------------------------------------------------------------------
    # Webhook management
    # ------------------------------------------------------------------

    def list_webhooks(self, project: str | None = None) -> list[dict[str, Any]]:
        """List all webhooks for a project."""
        encoded = self._encode_project(project)
        return self._get(f"/projects/{encoded}/hooks")

    def register_webhook(
        self,
        webhook_url: str,
        project: str | None = None,
        secret: str | None = None,
        events: list[str] | None = None,
    ) -> dict[str, Any]:
        """Register a webhook with the GitLab project.

        If *secret* is None, generates a random one and persists it
        to ~/.hive/configuration.json so the webhook handler can verify
        incoming payloads.
        """
        encoded = self._encode_project(project)
        events = events or self._config.enabled_events

        if secret is None:
            secret = secrets.token_hex(32)
            # Persist so webhook_handler can verify signatures later
            save_gitlab_config({"webhook_secret": secret})
            logger.info("Generated and saved webhook secret.")

        body: dict[str, Any] = {
            "url": webhook_url,
            "token": secret,
            "enable_ssl_verification": webhook_url.startswith("https"),
        }
        # Map event category names to GitLab API fields
        for event_name in events:
            body[event_name] = True

        result = self._get(f"/projects/{encoded}/hooks")
        # Check if webhook already exists for this URL
        if isinstance(result, list):
            for hook in result:
                if hook.get("url") == webhook_url:
                    logger.info("Webhook already registered (id=%s), updating.", hook["id"])
                    return self._put(f"/projects/{encoded}/hooks/{hook['id']}", json=body)

        return self._post(f"/projects/{encoded}/hooks", json=body)

    def delete_webhook(self, hook_id: int, project: str | None = None) -> dict[str, Any]:
        """Delete a webhook by ID."""
        encoded = self._encode_project(project)
        return self._delete(f"/projects/{encoded}/hooks/{hook_id}")

    # ------------------------------------------------------------------
    # Pipeline operations
    # ------------------------------------------------------------------

    def list_pipelines(
        self,
        project: str | None = None,
        status: str | None = None,
        per_page: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent pipelines."""
        encoded = self._encode_project(project)
        params: dict[str, Any] = {"per_page": per_page}
        if status:
            params["status"] = status
        return self._get(f"/projects/{encoded}/pipelines", params)

    def get_pipeline(self, pipeline_id: int, project: str | None = None) -> dict[str, Any]:
        encoded = self._encode_project(project)
        return self._get(f"/projects/{encoded}/pipelines/{pipeline_id}")

    def retry_pipeline(self, pipeline_id: int, project: str | None = None) -> dict[str, Any]:
        """Retry a failed pipeline."""
        encoded = self._encode_project(project)
        return self._post(f"/projects/{encoded}/pipelines/{pipeline_id}/retry")

    def get_pipeline_jobs(
        self, pipeline_id: int, project: str | None = None
    ) -> list[dict[str, Any]]:
        encoded = self._encode_project(project)
        return self._get(f"/projects/{encoded}/pipelines/{pipeline_id}/jobs")

    def get_job_log(self, job_id: int, project: str | None = None) -> str:
        """Get the raw log output of a CI job."""
        encoded = self._encode_project(project)
        resp = httpx.get(
            self._url(f"/projects/{encoded}/jobs/{job_id}/trace"),
            headers=self._headers(),
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            raise GitLabClientError(f"Failed to get job log: {resp.status_code}")
        return resp.text

    def retry_job(self, job_id: int, project: str | None = None) -> dict[str, Any]:
        encoded = self._encode_project(project)
        return self._post(f"/projects/{encoded}/jobs/{job_id}/retry")

    # ------------------------------------------------------------------
    # Merge request operations
    # ------------------------------------------------------------------

    def create_merge_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str = "",
        project: str | None = None,
        remove_source_branch: bool = True,
    ) -> dict[str, Any]:
        encoded = self._encode_project(project)
        return self._post(
            f"/projects/{encoded}/merge_requests",
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "remove_source_branch": remove_source_branch,
            },
        )

    # ------------------------------------------------------------------
    # Repository file operations (for automated fixes)
    # ------------------------------------------------------------------

    def create_branch(
        self, branch: str, ref: str = "main", project: str | None = None
    ) -> dict[str, Any]:
        encoded = self._encode_project(project)
        return self._post(
            f"/projects/{encoded}/repository/branches",
            json={"branch": branch, "ref": ref},
        )

    def commit_files(
        self,
        branch: str,
        commit_message: str,
        actions: list[dict[str, str]],
        project: str | None = None,
    ) -> dict[str, Any]:
        """Create a commit with one or more file actions.

        Each action dict: {"action": "update"|"create"|"delete",
                           "file_path": "...", "content": "..."}
        """
        encoded = self._encode_project(project)
        return self._post(
            f"/projects/{encoded}/repository/commits",
            json={
                "branch": branch,
                "commit_message": commit_message,
                "actions": actions,
            },
        )

    def get_file_content(
        self, file_path: str, ref: str = "main", project: str | None = None
    ) -> str:
        """Get raw file content from the repository."""
        encoded = self._encode_project(project)
        encoded_path = url_quote(file_path, safe="")
        resp = httpx.get(
            self._url(f"/projects/{encoded}/repository/files/{encoded_path}/raw"),
            headers=self._headers(),
            params={"ref": ref},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            raise GitLabClientError(f"Failed to get file: {resp.status_code}")
        return resp.text

    # ------------------------------------------------------------------
    # Security scan results
    # ------------------------------------------------------------------

    def get_vulnerability_findings(
        self, project: str | None = None, severity: str | None = None
    ) -> list[dict[str, Any]]:
        """List vulnerability findings for a project."""
        encoded = self._encode_project(project)
        params: dict[str, Any] = {"per_page": 100}
        if severity:
            params["severity"] = severity
        return self._get(f"/projects/{encoded}/vulnerability_findings", params)

    def get_pipeline_security_report(
        self, pipeline_id: int, project: str | None = None
    ) -> dict[str, Any]:
        """Get the security report summary for a pipeline."""
        encoded = self._encode_project(project)
        return self._get(f"/projects/{encoded}/pipelines/{pipeline_id}/security")
