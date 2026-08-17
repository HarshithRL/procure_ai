# OpenCode QuickStart — Procure AI

Welcome to the Procure AI workspace. This guide gets you oriented fast.

## First: Read AGENTS.md

```bash
cat AGENTS.md
```

This is your **source of truth** for workspace governance, tech stack, and constraints.

---

## Second: Use the Knowledge Graph

```powershell
cd .design_docs/assistent
graphify query "how do requirements flow to vendors?"
graphify explain "Vendor Comparison"
```

**Do this before grepping.** The graph has 63 nodes, 54 edges, 13 communities covering procurement domain, agent architecture, and infrastructure.

See `.opencode/mcps/graphify.md` for full reference.

---

## Third: Know the Folder Model

```
.design_docs/
  ├── Knowledge/              (READ-ONLY — source of truth)
  │   ├── 00 Usecase.md
  │   ├── 04 Agent System Arch.md
  │   └── ... (21 files total)
  │
  └── assistent/              (READ/WRITE — your workspace)
      ├── setup_details.md    (all commands: uv, git, flask, databricks)
      ├── graphify-out/       (knowledge graph)
      ├── tasks/              (your task plans)
      ├── handoffs/           (notes for next agent)
      └── scratch/            (temp debug logs)
```

**Rule**: Never edit Knowledge/. Everything else in assistent/ is yours.

---

## Fourth: Know Yourself

Two senior personas are available:

1. **senior-backend-developer** — API design, FastAPI/LangGraph, database architecture, production debugging
2. **senior-frontend-developer** — UI architecture, HTMX/Jinja/Alpine, HTML/CSS/TS, web vitals

Use them to plan before writing code. Example:
```
/load langgraph-architect
"Design the agent graph for Sprint 1 chat intake"
```

---

## Fifth: Next Agent's Job

When you finish a task:

1. **Stage & commit** your changes with conventional commits (`feat(scope):`, `fix:`, `docs:`)
2. **Handoff**: Create `.opencode/handoffs/handoff_<task>.md` with status, next steps, blockers
3. **Task plan**: Update or create `.design_docs/assistent/tasks/task_<sprint>_<feature>.md` (link from handoff)
4. **Push**: `git push origin main` (or your branch)

See `.opencode/handoffs/README.md` for template.

---

## Sixth: Common Commands

```powershell
# Python environment
uv venv .venv
uv add <package>
uv run pytest
uv run ruff check . --fix && uv run ruff format .

# Flask dev
uv run flask --app app run --debug --port 5000

# Databricks
databricks apps deploy ai-saas --source-code-path .

# Git
git status -sb
git add .
git commit -m "feat(scope): description"
git push origin main

# Graphify
cd .design_docs/assistent
graphify query "question"
graphify --update  (if docs changed)
```

See `.design_docs/assistent/setup_details.md` for the full reference.

---

## Seventh: The Stack (Sprint 1)

- **Backend**: Flask + LangChain + Databricks Apps
- **Python**: ≥3.11, managed via `uv`
- **Agents**: LangChain (multi-agent: Orchestrator, Controller, builders, decision intelligence)
- **Infrastructure**: Databricks (`ai-saas` app, `harshith_raghunath_d.vendor_agent` catalog, Lakebase Postgres)
- **Auth**: X-Forwarded headers (Databricks SSO proxy)
- **Frontend**: TBD (greenfield — no framework yet)

---

## Eighth: Current State

- **No application code yet**. `web_app/` is empty.
- **12 Sprint 1 deliverables** (see README.md:143): Flask app, user table, SSO headers, chat agent, model registry, HITL, etc.
- **Greenfield**: login → profile → dashboard → chat interface.

---

## Ninth: Blockers or Questions?

1. **Architecture**: Use `/graphify explain "<concept>"` or `/graphify query "<question>"`
2. **Commands**: Check `.design_docs/assistent/setup_details.md`
3. **Governance**: Check `AGENTS.md` Section 1
4. **Domain knowledge**: Check `.design_docs/Knowledge/` (READ-ONLY)

---

## Tenth: You're Ready

Go build. Leave handoff notes. Keep AGENTS.md and the graph in sync.

Questions? Run:
```
graphify query "how does X relate to Y?"
```

Good luck! 🚀
