"""GitLab integration for Maven — autonomous DevSecOps swarm.

Provides:
- GitLab API client for webhook registration and project management
- Webhook handler for receiving and verifying GitLab events
- Event router that maps GitLab events to Maven agent actions
- CLI commands for GitLab setup and management

All components are optional — Maven works without GitLab configured.
"""

from framework.gitlab.config import get_gitlab_config, is_gitlab_configured

__all__ = ["get_gitlab_config", "is_gitlab_configured"]
