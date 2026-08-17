# AGENTS.md — Procure AI Workspace

> **Instruction file for AI coding agents (Claude Code, OpenCode, Cursor AI).**
>
> Last updated: 2026-08-18 (Sprint 1 greenfield setup)

---

## 1. Workspace Governance

This repository follows the two-folder model defined in `.design_docs/Map.md`:

### `.design_docs/Knowledge/` — READ-ONLY
- **Source of truth** for business requirements, architecture, domain knowledge, and design decisions.
- **No agent may create, edit, or delete** any file here.
- Agents may read, search, and reference it.

### `.design_docs/assistent/` — READ/WRITE Control Plane
- **Centralized workspace** for agent task plans, logs, execution records, and skill configs.
- Agents may freely create and modify files here.
- **Subdirectories** (established structure):
  - `graphify-out/` — persistent knowledge graph (see Section 3)
  - `tasks/` — active/completed task plans (e.g. `task_sprint1_ui.md`)
  - `handoffs/` — inter-agent status notes
  - `scratch/` — temporary debug logs

---

## 2. Current State

**Application Code**: None yet. `web_app/` is empty.

**Repo State**:
- `pyproject.toml`: `dependencies = []`, `requires-python = ">=3.11"`
- `requirements.txt`: empty (managed via `uv`)
- 21 verified design documents, 4 git commits (all docs)
- Remote: `https://github.com/HarshithRL/procure_ai.git` (branch `main`)

**Do not assume Flask, FastAPI, or any frontend framework exists.** Sprint 1 is greenfield: login → profile → dashboard → chat interface.

---

## 3. Knowledge Graph — Your First Resource

**Location**: `.design_docs/assistent/graphify-out/`

Built from all 21 design docs (excluding Obsidian config and empty files). 63 nodes, 54 edges, 13 labeled communities covering:
- Procurement domain model
- Agent architecture
- Application UX & UI
- Knowledge graph & evidence
- Vendor intelligence
- Comparison engine
- Decision support
- Databricks infrastructure
- Development governance

**When to use the graph**:
- **Before grepping or searching docs**, run `/graphify query "<question>"` from `.design_docs/assistent/` workdir.
- Architecture questions ("how do requirements flow to vendors?", "what's the relationship between X and Y") — use the graph.
- Use `/graphify explain "<node-label>"` for plain-language node explanations.

**Graph files**:
- `graph.json` — raw knowledge graph (nodes, edges, communities)
- `GRAPH_REPORT.md` — human-readable audit report with god nodes and suggested questions
- `graph.html` — interactive visualization (open in browser, no server needed)
- `.graphify_labels.json` — community labels
- `cost.json` — token usage tracker

**Node ID convention** (for future reference when extracting/updating):
- Format: `{repo-relative-path}_{entity}` (lowercase, `[a-z0-9_]` only)
- Examples: `design_docs_knowledge_04_agent_system_arch_langchain_agent`, `readme_ai_powered_procurement`
- Non-alphanumerics (spaces, em-dashes, dots) → `_`
- **Deterministic**: same entity always produces same ID regardless of chunk/extraction order

---

## 4. Technology Stack (from Knowledge — verified source of truth)

### Infrastructure & Hosting
- **Databricks App** (NOT `procure-ai-workspace`; actual app is **`ai-saas`** per `Infra_and_auth_version/databricks/Workspace.md:11`)
- Host: `https://adb-7181820732839861.1.azuredatabricks.net/`
- **Unity Catalog**: `harshith_raghunath_d.vendor_agent`
- **UC Volumes** (app storage only): `/Volumes/harshith_raghunath_d/vendor_agent/application_storage`
- **Lakebase (Postgres)**: project `ds-vendor-agent` (for persistent OLTP if needed)
- **UC naming convention**: `app.user_table`, `agent.*` (from `Workspace.md:9`)

### Development & Deployment
- **Package manager**: `uv` (Python ≥3.11) — see full command reference in `.design_docs/assistent/setup_details.md`
- **Virtual environment**: `.venv/` (created via `uv venv .venv`)
- **Execution**: `uv run <cmd>` (no manual activation needed)
- **Git**: conventional-commit style (`feat(scope):`, `fix(auth):`, `docs(assistant):`) — see existing commits for examples

### Web Framework (from `README.md:149`)
- **Flask** — Flask app is Sprint 1 deliverable #2
- No frontend framework decided yet (greenfield)

### Agent & LLM (from `Knowledge/04 Agent System Arch.md` — subject to verification)
- **LangChain** explicitly mentioned in `__Core index.md:14` as part of agent stack
- Multi-agent system: Purchase Orchestrator, Procurement Controller, specialized builders (Intake, Document, Vendor, Evidence, Knowledge)
- Evaluation/Comparison/Risk/Decision intelligence agents
- Model registry integration (Sprint 1 deliverable #7)

### Code Quality & Style
- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Testing**: `uv run pytest` (when tests are written)
- **Type checking**: `uv run mypy src/` (when typed code exists)

---

## 5. Repo Constraints & Gotchas

### Do NOT scan `.design_docs/.obsidian/`
- Contains ~6.8 MB of tracked minified vendor plugin bundles (JS).
- Excluded from graphify corpus by design.
- Skip in any file search, codebase scan, or build operation.

### Databricks App Deployment
- `setup_details.md:226` references app `procure-ai-workspace` → **incorrect** (legacy).
- **Correct app name**: `ai-saas` (from Knowledge source of truth).
- Use Databricks CLI: `databricks apps deploy ai-saas --source-code-path .`
- Workspace notebook location: `/Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent`

### X-Forwarded Header for SSO
- Sprint 1 deliverable #4.
- Databricks Apps inject `X-Forwarded-User`, `X-Forwarded-Email`, `X-Forwarded-Preferred-Username` headers for authenticated users.
- Flask app must extract and trust these headers for user identification.
- Test locally with `curl`:
  ```powershell
  curl -X GET http://127.0.0.1:5000/api/profile `
    -H "X-Forwarded-User: user@company.com" `
    -H "X-Forwarded-Email: user@company.com"
  ```

### No Obsidian Workspace Artifacts in Git
- `.gitignore` correctly ignores `.obsidian/workspace.json` to prevent merge conflicts.
- Keep this rule — do not commit Obsidian UI state.

---

## 6. Sprint 1 Deliverables Reference

Full checklist in `README.md:143`:

1. Deploy Databricks App
2. Flask App (core framework)
3. User Table (model & persistence)
4. X-Forwarded Header Handling (SSO proxy headers)
5. Telemetry (logging & metrics)
6. Chat Agent (conversational core)
7. Model Registry (LLM endpoint config)
8. Context Management (memory buffer, token budget, history)
9. User Tools & MCP (SharePoint, Outlook, OneDrive, user memory)
10. HITL (human-in-the-loop approval & clarifications)
11. Session Management (multi-turn persistence)
12. Templates (prompt templates & artifact schemas)

---

## 7. Commands Cheat Sheet

See **full reference** in `.design_docs/assistent/setup_details.md` (Sections 2–4) for comprehensive Git, uv, Flask, and Databricks CLI commands.

**Common**:
```powershell
# Setup venv
uv venv .venv
.venv\Scripts\Activate.ps1  # or source .venv/bin/activate on Linux

# Add/remove dependency
uv add <package>
uv remove <package>

# Run Flask dev server (hot reload)
uv run flask --app app run --debug --port 5000

# Deploy to Databricks App
databricks apps deploy ai-saas --source-code-path .

# Graphify: query knowledge graph
cd .design_docs/assistent
graphify query "how do requirements flow to vendors?"
graphify explain "Vendor Comparison"

# Git
git status -sb
git add .
git commit -m "feat(auth): implement x-forwarded header parsing"
git push origin feature/branch
```

---

## 8. For Future Agents

**Before you start**:
1. Read this file.
2. Check `.design_docs/Knowledge/` for context (READ-ONLY).
3. Run `/graphify query "<your-question>"` from `.design_docs/assistent/` — the graph is your map.
4. Create a task plan in `.design_docs/assistent/tasks/` linking to this task.

**When you finish**:
1. Commit changes to `main` with a conventional commit message.
2. Leave a handoff note in `.design_docs/assistent/handoffs/` if another agent needs to continue.
3. Do not modify Knowledge files — ever.

---

## 9. Sources of Truth

- **Business & Product**: `.design_docs/Knowledge/` (READ-ONLY)
- **Command Reference**: `.design_docs/assistent/setup_details.md`
- **Agent Governance**: `.design_docs/Map.md`
- **Knowledge Graph**: `.design_docs/assistent/graphify-out/` (query via `/graphify` or read `graph.json`)
- **Remote Repo**: `https://github.com/HarshithRL/procure_ai.git` (main branch)

---

*Questions? Use `/graphify` on the knowledge graph first.*
