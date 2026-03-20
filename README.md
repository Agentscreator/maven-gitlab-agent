<p align="center">
  <h1 align="center">Maven</h1>
  <p align="center"><strong>Autonomous DevSecOps Swarm for GitLab</strong></p>
  <p align="center"><em>Your GitLab project never sleeps. Neither does Maven.</em></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License" />
  <img src="https://img.shields.io/badge/GitLab-Duo%20Agent%20Platform-FC6D26?style=flat-square&logo=gitlab" alt="GitLab Duo" />
  <img src="https://img.shields.io/badge/Anthropic-Claude%20Queen-d4a574?style=flat-square" alt="Anthropic Claude" />
  <img src="https://img.shields.io/badge/GitLab%20AI%20Hackathon-Submission-blueviolet?style=flat-square" alt="Hackathon" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Multi--Agent-Swarm-blue?style=flat-square" alt="Multi-Agent" />
  <img src="https://img.shields.io/badge/Self--Healing-Pipelines-brightgreen?style=flat-square" alt="Self-Healing" />
  <img src="https://img.shields.io/badge/Human--in--the--Loop-orange?style=flat-square" alt="HITL" />
  <img src="https://img.shields.io/badge/Green%20Agent-Routing-green?style=flat-square" alt="Green Routing" />
  <img src="https://img.shields.io/badge/Zero--Hardcode-Workflows-purple?style=flat-square" alt="Zero Hardcode" />
</p>

---

## Overview

Maven is an autonomous, self-healing multi-agent swarm that lives inside your GitLab environment. It watches your software development lifecycle in real time — reacting to failing pipelines, new security vulnerabilities, stale merge requests, and unreviewed issues — and takes targeted action through the **GitLab Duo Agent Platform** without waiting for a human to notice.

Where traditional AI tools answer questions, **Maven answers situations**. It is outcome-driven, not prompt-driven. You don't ask Maven to do something; Maven recognizes that something needs to be done and does it.

Maven is built on top of the open-source [Hive](https://github.com/aden-hive/hive) agent framework by Aden, adapted and specialized for the GitLab SDLC. **Claude (Anthropic) serves as the Queen** — the central reasoning and code-generation agent that designs, coordinates, and evolves the entire worker swarm.

---

## The Problem Maven Solves

Development teams face what we call the **AI Paradox**: AI writes code faster than ever, but the surrounding process — security reviews, test coverage, CI/CD failures, issue triage, compliance checks — hasn't kept pace. The bottleneck has shifted from writing code to everything around it.

A typical week on a mid-sized GitLab project:

- A SAST scan fires 12 new vulnerabilities. They sit unreviewed for **4 days**.
- A pipeline breaks at 2am. No one sees it until standup. The fix takes 20 minutes but costs **8 hours of delay**.
- 60 issues are opened. 40 are **unlabeled, unassigned, and missing acceptance criteria**.
- An MR violates a compliance policy. It gets merged anyway because **no one checked**.

AI chatbots don't solve this. They wait to be asked. Maven doesn't wait.

---

## How Maven Works

### The Core Loop

```
GitLab Event Fires
→ Queen Agent (Claude) interprets the event and defines the goal
→ Queen generates a worker graph — which agents are needed and in what order
→ Worker swarm executes in parallel using GitLab Duo Agent Platform
→ Results are evaluated against the original goal
→ Success → Close the loop, log outcome, update memory
→ Failure → Capture failure data, Queen evolves the graph, redeploy
→ Human-in-the-Loop node escalates to a human if confidence is below threshold
```

### GitLab Event Triggers

| GitLab Event | Maven Goal |
|---|---|
| Security scan finds vulnerability | Analyze, patch, open MR, notify |
| Pipeline fails | Diagnose root cause, attempt fix, retry or escalate |
| Issue opened | Triage, label, assign, draft acceptance criteria |
| MR opened | Review for compliance, test coverage, code quality |
| Test coverage drops below threshold | Identify uncovered code, generate tests, commit |
| Stale MR idle > N days | Summarize, ping assignee, or close with explanation |

### The Queen Agent (Claude)

The Queen is the brain of Maven. Powered by Claude (Anthropic), the Queen is responsible for:

- Interpreting the incoming GitLab event and inferring the correct goal
- Dynamically generating the worker graph — deciding which specialist agents to spawn, in what order, with what context
- Evaluating outcomes against the original goal
- On failure: analyzing what went wrong, evolving the worker graph, and redeploying

The Queen never executes actions directly. It reasons, plans, and delegates.

### Worker Agent Castes

Maven ships five pre-built worker castes, each a specialist with a narrow responsibility:

**Security Worker** — Reads SAST/DAST scan results from GitLab. Identifies affected files and vulnerable code patterns. Drafts a patch, commits it to a fix branch, opens an MR, and links it to the original security finding. If the patch breaks tests, the failure is fed back to the Queen for a revised strategy.

**Test Worker** — Analyzes code coverage reports and identifies untested functions or branches. Generates targeted test cases using the language and framework already present in the repo. Commits the new tests and runs the pipeline to confirm coverage improvement.

**Triage Worker** — Reads newly opened issues. Applies appropriate labels based on content analysis, assigns to the relevant team member based on CODEOWNERS or past contribution history, drafts a structured comment with clarifying questions or acceptance criteria, and links related issues or MRs.

**Deploy Worker** — Monitors pipeline failures. Reads the job logs to identify the root cause (flaky test, dependency conflict, environment misconfiguration, etc.). Attempts the appropriate fix — retrying the job, patching a config file, updating a dependency version, or rolling back the offending commit. Escalates to a human when the failure is ambiguous.

**Compliance Worker** — Runs on every opened MR. Checks the diff against a configurable policy ruleset (e.g., no hardcoded secrets, required reviewers present, changelog updated, no direct pushes to protected branches). Posts a structured compliance report as an MR comment. Blocks merge via GitLab approval rules if critical violations are found.

---

## Architecture

```
Maven Control Plane
├── GitLab Webhooks → Event Router (classifies & queues)
├── Queen Agent (Claude)
│   ├── Goal interpretation
│   ├── Graph generation
│   ├── Outcome evaluation
│   └── Self-healing / evolve
├── Worker Swarm
│   ├── Security Worker
│   ├── Test Worker
│   ├── Triage Worker
│   ├── Deploy Worker
│   └── Compliance Worker
├── GitLab Duo Agent Platform (action executor)
├── Human-in-the-Loop Escalation Node
└── Real-time Observability Dashboard
    ├── WebSocket streaming
    ├── Cost tracking
    └── Event logs
```

### Technology Stack

| Layer | Technology |
|---|---|
| Queen Agent (reasoning) | Claude 3.5 Sonnet / Claude 3 Opus via Anthropic API |
| Worker execution | GitLab Duo Agent Platform |
| Framework runtime | Hive (Aden) — Python 3.11+ |
| LLM routing | LiteLLM (model-agnostic) |
| Tool protocol | MCP (Model Context Protocol) |
| Event ingestion | GitLab Webhooks → Event Router |
| Observability | WebSocket streaming dashboard |
| Credential storage | Encrypted local credential store (`~/.hive/credentials`) |
| Green routing | Small models (Haiku / Gemini Flash) for low-complexity tasks |

---

## Key Features

### Self-Healing Swarm
When a worker agent fails, Maven doesn't stop. The Queen captures the full failure context (the goal, the worker graph, the error output, the GitLab API response), reasons about what went wrong, rewrites the relevant worker's instructions or graph connections, and redeploys. This loop runs automatically within configurable retry limits.

### Dynamic Graph Generation
Maven does not have hardcoded workflows. The Queen generates a fresh agent graph for each event based on context. A security vulnerability in a Go service gets a different worker configuration than one in a Python script. The graph is always appropriate to the situation.

### Human-in-the-Loop Escalation
Every workflow has a configurable confidence threshold. When a worker's output falls below that threshold, execution pauses and a structured summary is posted as a GitLab comment or sent via notification, routing the decision to a human. Timeouts and escalation policies ensure nothing gets stuck permanently.

### Green Agent Routing
Maven routes tasks by complexity. Triage and labeling tasks use lightweight, low-cost models. Security patching and architectural reasoning use Claude. A real-time cost dashboard shows spend per event type, per agent, and per repository. Budget caps prevent runaway costs.

### SDK-Wrapped Nodes
Every worker agent has access to shared memory (context across the swarm), local rolling memory (context within its own task), full tool access (GitLab API, file system, browser if needed), and LLM access — all out of the box through the Hive SDK.

### Zero-Hardcode Philosophy
Connection code between nodes is generated by the Queen. You don't wire up workflows manually. You configure Maven's policies and Maven figures out the rest.

---

## Installation & Setup

**1. Clone Maven**
```bash
git clone https://github.com/Agentscreator/maven-gitlab-agent.git
cd maven-gitlab-agent
```

**2. Run quickstart** (sets up all environments, credential store, and LLM config)
```bash
./quickstart.sh
```

**3. Configure your GitLab connection**
```bash
maven config set gitlab.token YOUR_PERSONAL_ACCESS_TOKEN
maven config set gitlab.url https://gitlab.com
maven config set anthropic.key YOUR_ANTHROPIC_API_KEY
```

**4. Register Maven's webhook with your GitLab project**
```bash
maven gitlab register --project your-namespace/your-project
```

**5. Open the Maven dashboard**
```bash
maven open
```

Once registered, Maven begins listening. Workers activate on the first matching event.

---

## Configuration Reference

Maven's behavior is controlled through a single YAML policy file:

```yaml
queen:
  model: claude-3-5-sonnet-20241022
  max_retries: 3
  confidence_threshold: 0.75

workers:
  security:
    enabled: true
    auto_commit: true
    require_human_approval_for: ["critical", "high"]
  test:
    enabled: true
    min_coverage_delta: 5
  triage:
    enabled: true
    assign_from: codeowners
  deploy:
    enabled: true
    auto_retry_limit: 2
  compliance:
    enabled: true
    policy_file: .maven/compliance-rules.yaml
    block_on: ["secrets_detected", "required_reviewer_missing"]

green_routing:
  enabled: true
  simple_tasks_model: claude-haiku-3
  complex_tasks_model: claude-3-5-sonnet-20241022
  cost_cap_daily_usd: 20.00

human_in_the_loop:
  notification_channel: gitlab_comment
  escalation_timeout_minutes: 60
  escalation_fallback: assign_to_maintainer
```

---

## Roadmap

| Version | Milestone |
|---|---|
| **v1.0** (Hackathon) | Five worker castes, Queen on Claude, GitLab Duo execution, self-healing loop, green routing, human-in-the-loop, real-time dashboard |
| **v1.1** | Custom worker creation via natural language. Queen interviews user, generates and deploys the new caste |
| **v1.2** | Cross-project swarms. Maven watches an entire GitLab group and coordinates workers across multiple repositories |
| **v1.3** | Memory and learning. Maven builds a per-repository knowledge base of past failures, successful fixes, and team preferences |
| **v2.0** | Maven Marketplace. Share worker caste templates with the community |

---

## Acknowledgements

Maven is built on the open-source [Hive](https://github.com/aden-hive/hive) framework by Aden, adapted and extended for the GitLab SDLC. It uses the **GitLab Duo Agent Platform** for action execution and **Claude (Anthropic)** as the Queen reasoning agent.

---

<p align="center">
  <strong>Maven — Because your codebase deserves a teammate that never clocks out.</strong>
</p>

<p align="center">
  <em>GitLab AI Hackathon Submission</em>
</p>
