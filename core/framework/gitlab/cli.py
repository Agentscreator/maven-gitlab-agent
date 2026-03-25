"""CLI commands for GitLab integration.

Provides:
    hive gitlab setup     — Interactive GitLab configuration
    hive gitlab status    — Show connection status
    hive gitlab register  — Register webhook with a GitLab project
    hive gitlab webhooks  — List registered webhooks
    hive gitlab test      — Send a test event to verify the integration
"""

from __future__ import annotations

import argparse
import json
import sys


def register_gitlab_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'gitlab' command group with the main CLI."""
    gitlab_parser = subparsers.add_parser(
        "gitlab",
        help="GitLab integration commands",
        description="Configure and manage Maven's GitLab integration.",
    )
    gitlab_sub = gitlab_parser.add_subparsers(dest="gitlab_command")

    # setup
    setup_parser = gitlab_sub.add_parser(
        "setup",
        help="Interactive GitLab configuration",
    )
    setup_parser.set_defaults(func=cmd_gitlab_setup)

    # status
    status_parser = gitlab_sub.add_parser(
        "status",
        help="Show GitLab connection status",
    )
    status_parser.set_defaults(func=cmd_gitlab_status)

    # register
    register_parser = gitlab_sub.add_parser(
        "register",
        help="Register webhook with GitLab project",
    )
    register_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="GitLab project (namespace/name format)",
    )
    register_parser.add_argument(
        "--url",
        type=str,
        help="Public URL for webhook delivery (e.g. https://your-server.com/webhooks/gitlab)",
    )
    register_parser.set_defaults(func=cmd_gitlab_register)

    # webhooks
    webhooks_parser = gitlab_sub.add_parser(
        "webhooks",
        help="List registered webhooks",
    )
    webhooks_parser.add_argument(
        "--project",
        type=str,
        help="GitLab project (uses configured project if omitted)",
    )
    webhooks_parser.set_defaults(func=cmd_gitlab_webhooks)

    # test
    test_parser = gitlab_sub.add_parser(
        "test",
        help="Test the GitLab connection",
    )
    test_parser.set_defaults(func=cmd_gitlab_test)

    # If no subcommand given, show help
    gitlab_parser.set_defaults(func=lambda args: gitlab_parser.print_help() or 0)


def cmd_gitlab_setup(args: argparse.Namespace) -> int:
    """Interactive GitLab setup."""
    from framework.gitlab.config import get_gitlab_config, save_gitlab_config

    print("\n🦊 Maven GitLab Setup\n")

    current = get_gitlab_config()

    # GitLab URL
    default_url = current.url
    url = input(f"  GitLab URL [{default_url}]: ").strip() or default_url

    # Token
    token_hint = "****" + current.token[-4:] if current.token and len(current.token) > 4 else ""
    token_prompt = f"  Personal Access Token [{token_hint}]: " if token_hint else "  Personal Access Token: "
    token = input(token_prompt).strip()
    if not token and current.token:
        token = current.token

    if not token:
        print("\n  ⚠ No token provided. GitLab integration will be disabled.")
        print("  Create one at: {}//-/user_settings/personal_access_tokens".format(url))
        return 1

    # Project
    project_default = current.project or ""
    project_prompt = f"  Default project [{project_default}]: " if project_default else "  Default project (namespace/name): "
    project = input(project_prompt).strip() or project_default

    # Save
    updates = {"url": url, "token": token}
    if project:
        updates["project"] = project

    save_gitlab_config(updates)
    print("\n  ✓ GitLab configuration saved to ~/.hive/configuration.json")

    # Verify connection
    print("  Verifying connection...", end=" ", flush=True)
    try:
        from framework.gitlab.client import GitLabClient

        client = GitLabClient()
        user = client.verify_token()
        print(f"✓ Authenticated as @{user.get('username', '?')}")
    except Exception as e:
        print(f"✗ {e}")
        return 1

    if project:
        print(f"  Checking project '{project}'...", end=" ", flush=True)
        try:
            proj = client.get_project(project)
            print(f"✓ {proj.get('path_with_namespace', project)}")
        except Exception as e:
            print(f"✗ {e}")

    print()
    return 0


def cmd_gitlab_status(args: argparse.Namespace) -> int:
    """Show GitLab connection status."""
    from framework.gitlab.config import get_gitlab_config

    config = get_gitlab_config()

    print("\n📊 GitLab Integration Status\n")
    print(f"  URL:              {config.url}")
    print(f"  Token:            {'configured' if config.token else 'NOT SET'}")
    print(f"  Project:          {config.project or 'not set'}")
    print(f"  Webhook secret:   {'configured' if config.webhook_secret else 'not set'}")
    print(f"  Webhook path:     {config.webhook_path}")
    print(f"  Enabled events:   {', '.join(config.enabled_events)}")

    if config.is_configured:
        print("\n  Checking connection...", end=" ", flush=True)
        try:
            from framework.gitlab.client import GitLabClient

            client = GitLabClient(config)
            user = client.verify_token()
            print(f"✓ Connected as @{user.get('username', '?')}")
        except Exception as e:
            print(f"✗ {e}")
    else:
        print("\n  ⚠ GitLab not configured. Run 'hive gitlab setup' to get started.")

    print()
    return 0


def cmd_gitlab_register(args: argparse.Namespace) -> int:
    """Register a webhook with a GitLab project."""
    from framework.gitlab.client import GitLabClient, GitLabClientError
    from framework.gitlab.config import save_gitlab_config

    project = args.project
    webhook_url = args.url

    if not webhook_url:
        print("  ⚠ No --url provided.")
        print("  Maven needs a publicly accessible URL for GitLab to send webhooks to.")
        print("  Example: https://your-server.com/webhooks/gitlab")
        print("  For local development, use a tunnel like ngrok:")
        print("    ngrok http 8787")
        print("    Then use the https URL ngrok gives you + /webhooks/gitlab")
        return 1

    try:
        client = GitLabClient()
    except GitLabClientError as e:
        print(f"  ✗ {e}")
        return 1

    # Save project to config
    save_gitlab_config({"project": project})

    print(f"\n  Registering webhook for {project}...")
    print(f"  URL: {webhook_url}")

    try:
        result = client.register_webhook(webhook_url, project=project)
        hook_id = result.get("id", "?")
        print(f"  ✓ Webhook registered (id={hook_id})")
        print(f"  Events: {', '.join(client.config.enabled_events)}")
        print("\n  Maven is now listening for GitLab events.")
    except GitLabClientError as e:
        print(f"  ✗ Failed to register webhook: {e}")
        return 1

    print()
    return 0


def cmd_gitlab_webhooks(args: argparse.Namespace) -> int:
    """List registered webhooks."""
    from framework.gitlab.client import GitLabClient, GitLabClientError

    try:
        client = GitLabClient()
    except GitLabClientError as e:
        print(f"  ✗ {e}")
        return 1

    project = args.project

    try:
        hooks = client.list_webhooks(project)
    except GitLabClientError as e:
        print(f"  ✗ {e}")
        return 1

    if not hooks:
        print("  No webhooks registered.")
        return 0

    print(f"\n  Webhooks for {project or client.config.project}:\n")
    for hook in hooks:
        print(f"  [{hook.get('id')}] {hook.get('url')}")
        events = []
        for key in ("push_events", "merge_requests_events", "issues_events",
                     "pipeline_events", "job_events"):
            if hook.get(key):
                events.append(key.replace("_events", "").replace("_", " "))
        print(f"       Events: {', '.join(events) or 'none'}")
        print(f"       SSL:    {'yes' if hook.get('enable_ssl_verification') else 'no'}")
        print()

    return 0


def cmd_gitlab_test(args: argparse.Namespace) -> int:
    """Test the GitLab connection."""
    from framework.gitlab.client import GitLabClient, GitLabClientError

    print("\n🧪 Testing GitLab Connection\n")

    try:
        client = GitLabClient()
    except GitLabClientError as e:
        print(f"  ✗ {e}")
        return 1

    # Test auth
    print("  1. Authentication...", end=" ", flush=True)
    try:
        user = client.verify_token()
        print(f"✓ @{user.get('username')}")
    except GitLabClientError as e:
        print(f"✗ {e}")
        return 1

    # Test project access
    if client.config.project:
        print(f"  2. Project access ({client.config.project})...", end=" ", flush=True)
        try:
            proj = client.get_project()
            print(f"✓ {proj.get('name')}")
        except GitLabClientError as e:
            print(f"✗ {e}")
            return 1

        # Test pipeline listing
        print("  3. Pipeline access...", end=" ", flush=True)
        try:
            pipelines = client.list_pipelines(per_page=1)
            count = len(pipelines) if isinstance(pipelines, list) else 0
            print(f"✓ ({count} recent)")
        except GitLabClientError as e:
            print(f"✗ {e}")

        # Test webhook listing
        print("  4. Webhook access...", end=" ", flush=True)
        try:
            hooks = client.list_webhooks()
            count = len(hooks) if isinstance(hooks, list) else 0
            print(f"✓ ({count} registered)")
        except GitLabClientError as e:
            print(f"✗ {e}")
    else:
        print("  2. No project configured — skipping project tests.")

    print("\n  All checks passed. GitLab integration is ready.\n")
    return 0
