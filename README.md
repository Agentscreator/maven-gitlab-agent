<div align="center">

<br/>

```
███╗   ███╗ █████╗ ██╗   ██╗███████╗███╗   ██╗
████╗ ████║██╔══██╗██║   ██║██╔════╝████╗  ██║
██╔████╔██║███████║██║   ██║█████╗  ██╔██╗ ██║
██║╚██╔╝██║██╔══██║╚██╗ ██╔╝██╔══╝  ██║╚██╗██║
██║ ╚═╝ ██║██║  ██║ ╚████╔╝ ███████╗██║ ╚████║
╚═╝     ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝
```

### **Autonomous DevSecOps Swarm for GitLab**

*Your GitLab project never sleeps. Neither does Maven.*

<br/>

[![License](https://img.shields.io/badge/License-Apache_2.0-brown.svg?style=for-the-badge)](LICENSE)
[![GitLab](https://img.shields.io/badge/GitLab-Duo_Agent_Platform-FC6D26?style=for-the-badge&logo=gitlab&logoColor=white)](https://gitlab.com)
[![Claude](https://img.shields.io/badge/Powered_by-Claude_Queen-8B4513?style=for-the-badge)](https://anthropic.com)
[![Hackathon](https://img.shields.io/badge/GitLab_AI_Hackathon-2026_Submission-6B2D2D?style=for-the-badge)](https://gitlab.com)

<br/>

[![Self-Healing](https://img.shields.io/badge/⚙_Self--Healing-Pipelines-1a0a00?style=flat-square&labelColor=3d1f00&color=6b3300)](.)
[![Multi-Agent](https://img.shields.io/badge/🐝_Multi--Agent-Swarm-1a0a00?style=flat-square&labelColor=3d1f00&color=6b3300)](.)
[![HITL](https://img.shields.io/badge/👁_Human--in--the--Loop-Escalation-1a0a00?style=flat-square&labelColor=3d1f00&color=6b3300)](.)
[![Green](https://img.shields.io/badge/🌿_Green_Agent-Routing-1a0a00?style=flat-square&labelColor=3d1f00&color=6b3300)](.)

</div>

<br/>

---

<br/>

## `>_ what is maven`

Maven is an **autonomous, self-healing multi-agent swarm** that lives inside your GitLab environment. It watches your software development lifecycle in real time — reacting to failing pipelines, new security vulnerabilities, stale merge requests, and unreviewed issues — and takes targeted action through the **GitLab Duo Agent Platform** without waiting for a human to notice.

> Where traditional AI tools answer questions, **Maven answers situations.**
> It is outcome-driven, not prompt-driven. You don't ask Maven to do something —
> Maven recognizes that something needs to be done and does it.

**Claude (Anthropic) is the Queen** — the central reasoning and coordination agent that designs, directs, and evolves the entire worker swarm.

<br/>

---

<br/>

## `>_ the problem`

Development teams face what we call the **AI Paradox**: AI writes code faster than ever, but the surrounding process — security reviews, test coverage, CI/CD failures, issue triage, compliance checks — hasn't kept pace. The bottleneck has shifted from writing code to everything around it.

<br/>

<div align="center">

| What happens | The cost |
|:---|:---|
| 🔴 SAST scan fires 12 vulnerabilities | Sit unreviewed for **4 days** |
| 🔴 Pipeline breaks at 2am | No one sees it until standup — **8 hours lost** |
| 🔴 60 issues opened in a sprint | 40 are **unlabeled, unassigned, no criteria** |
| 🔴 MR violates compliance policy | Gets merged anyway — **no one checked** |

</div>

<br/>

> AI chatbots don't solve this. They wait to be asked. **Maven doesn't wait.**

<br/>

---

<br/>

## `>_ how it works`

### The Core Loop

```
  GitLab Event Fires
        │
        ▼
  ┌─────────────────────────────────────────┐
  │        Queen Agent  (Claude)            │
  │  · Interprets event → defines goal      │
  │  · Generates worker graph               │
  │  · Evaluates outcome                    │
  │  · On failure: evolves graph, redeploys │
  └──────────────────┬──────────────────────┘
                     │
        ┌────────────▼────────────┐
        │     Worker Swarm        │
        │  (parallel execution)   │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  GitLab Duo Agent       │
        │  Platform (executor)    │
        └────────────┬────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      ✅ Success            ⚠️  Low confidence
   Close loop              Human-in-the-Loop
   Log & update            Escalation Node
```

<br/>

### Event → Action Map

<div align="center">

| 🔔 GitLab Event | ⚡ Maven Response |
|:---|:---|
| Security scan finds vulnerability | Analyze · patch · open MR · notify |
| Pipeline fails | Diagnose root cause · fix · retry or escalate |
| Issue opened | Triage · label · assign · draft acceptance criteria |
| MR opened | Review compliance · test coverage · code quality |
| Coverage drops below threshold | Find uncovered code · generate tests · commit |
| MR idle > N days | Summarize · ping assignee · or close with explanation |

</div>

<br/>

---

<br/>

## `>_ worker castes`

<br/>

<div align="center">

```
┌──────────────────────────────────────────────────────────────────┐
│                        MAVEN SWARM                               │
│                                                                  │
│   👑  QUEEN  (Claude)                                            │
│       Reasons · Plans · Delegates · Evolves                      │
│                                                                  │
│   ├── 🛡️  Security Worker                                        │
│   │       SAST/DAST → patch → MR → link to finding              │
│   │                                                              │
│   ├── 🧪  Test Worker                                            │
│   │       Coverage gaps → generate tests → confirm green         │
│   │                                                              │
│   ├── 🏷️  Triage Worker                                          │
│   │       Issues → label → assign → acceptance criteria          │
│   │                                                              │
│   ├── 🚀  Deploy Worker                                          │
│   │       Pipeline logs → root cause → fix → retry               │
│   │                                                              │
│   └── ✅  Compliance Worker                                      │
│           MR diff → policy check → report → block if critical    │
└──────────────────────────────────────────────────────────────────┘
```

</div>

<br/>

---

<br/>

## `>_ architecture`

```
Maven Control Plane
├── GitLab Webhooks ──→ Event Router  (classify & queue)
│
├── 👑 Queen Agent (Claude)
│   ├── Goal interpretation
│   ├── Dynamic graph generation
│   ├── Outcome evaluation
│   └── Self-healing / graph evolution
│
├── 🐝 Worker Swarm
│   ├── Security Worker
│   ├── Test Worker
│   ├── Triage Worker
│   ├── Deploy Worker
│   └── Compliance Worker
│
├── GitLab Duo Agent Platform  (action executor)
├── Human-in-the-Loop Escalation Node
│
└── 📊 Real-time Observability Dashboard
    ├── WebSocket streaming
    ├── Cost tracking per agent / event type
    └── Execution logs
```

<br/>

### Stack

<div align="center">

| Layer | Technology |
|:---|:---|
| Queen reasoning | Claude 3.5 Sonnet / Claude 3 Opus — Anthropic API |
| Worker execution | GitLab Duo Agent Platform |
| Runtime | Python 3.11+ |
| LLM routing | LiteLLM (model-agnostic) |
| Tool protocol | MCP — Model Context Protocol |
| Event ingestion | GitLab Webhooks → Event Router |
| Observability | WebSocket streaming dashboard |
| Credentials | Encrypted store at `~/.maven/credentials` |
| Green routing | Haiku / Gemini Flash for low-complexity tasks |

</div>

<br/>

---

<br/>

## `>_ key features`

<br/>

**`⚙️ Self-Healing Swarm`**
When a worker fails, Maven doesn't stop. The Queen captures the full failure context, reasons about what went wrong, rewrites the relevant worker's instructions or graph connections, and redeploys — automatically, within configurable retry limits.

**`🔀 Dynamic Graph Generation`**
No hardcoded workflows. The Queen generates a fresh agent graph for every event based on context. A vulnerability in a Go service gets a different worker configuration than one in a Python script.

**`👁 Human-in-the-Loop Escalation`**
Every workflow has a configurable confidence threshold. Below it, execution pauses and a structured summary is posted as a GitLab comment, routing the decision to a human. Timeouts and fallback policies ensure nothing gets stuck.

**`🌿 Green Agent Routing`**
Tasks are routed by complexity. Triage uses lightweight, low-cost models. Security patching uses Claude. A live cost dashboard shows spend per event type, per agent, per repo. Daily budget caps prevent runaway costs.

**`🧩 SDK-Wrapped Nodes`**
Every worker has shared swarm memory, local rolling memory, full tool access (GitLab API, filesystem, browser), and LLM access — all out of the box.

**`∅ Zero-Hardcode Philosophy`**
Connection code between nodes is generated by the Queen. You configure policies. Maven figures out the rest.

<br/>

---

<br/>

## `>_ quickstart`

```bash
# 1. Clone
git clone https://github.com/Agentscreator/maven-gitlab-agent.git
cd maven-gitlab-agent

# 2. Install
./quickstart.sh

# 3. Connect GitLab + Anthropic
maven config set gitlab.token   YOUR_GITLAB_TOKEN
maven config set gitlab.url     https://gitlab.com
maven config set anthropic.key  YOUR_ANTHROPIC_API_KEY

# 4. Register webhook
maven gitlab register --project your-namespace/your-project

# 5. Launch
maven open
```

> Once registered, Maven begins listening. Workers activate on the first matching event.

<br/>

---

<br/>

## `>_ configuration`

```yaml
# .maven/policy.yaml

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

<br/>

---

<br/>

## `>_ roadmap`

<div align="center">

```
v1.0  ████████████████████  NOW
      Five worker castes · Queen on Claude · GitLab Duo
      Self-healing · Green routing · HITL · Dashboard

v1.1  ████████████░░░░░░░░  NEXT
      Custom workers via natural language
      "Create a worker that enforces our API naming conventions"

v1.2  ████████░░░░░░░░░░░░  SOON
      Cross-project swarms across an entire GitLab group

v1.3  ██████░░░░░░░░░░░░░░  LATER
      Per-repo memory — learns from past failures over time

v2.0  ████░░░░░░░░░░░░░░░░  FUTURE
      Maven Marketplace — community worker caste templates
```

</div>

<br/>

---

<br/>

<div align="center">

**Maven** uses the [GitLab Duo Agent Platform](https://gitlab.com) for execution
and [Claude (Anthropic)](https://anthropic.com) as the Queen reasoning agent.

<br/>

```
Because your codebase deserves a teammate that never clocks out.
```

<br/>

*GitLab AI Hackathon — 2026 Submission*

</div>
