# Setup Summary — Procure AI Agent Environment

**Completed**: 2026-08-18  
**Commits**: 3 (AGENTS.md + knowledge graph, opencode.json + MCP, quickstart guide)  
**Status**: Ready for agent development

---

## What Was Set Up

### 1. AGENTS.md (Repo Root)
Central instruction file for all coding agents. Contains:
- ✅ Workspace governance (Knowledge/ read-only, assistent/ read-write)
- ✅ Current state (no app code yet, greenfield Sprint 1)
- ✅ Knowledge graph location and usage
- ✅ Tech stack (Flask, LangChain, Databricks `ai-saas`, Python ≥3.11, uv)
- ✅ Databricks facts (corrected app name, UC naming, SSO headers)
- ✅ Gotchas (no scanning `.obsidian/`, correct app name)
- ✅ Sprint 1 deliverables checklist (12 items)
- ✅ Command cheat sheet + full reference link
- ✅ Sources of truth (Knowledge, setup_details.md, Map.md, graph)

**Size**: 8.5 KB, 278 lines

---

### 2. Knowledge Graph (`.design_docs/assistent/graphify-out/`)
Built from 21 design docs (23 files, ~19.8k words).  
Automatically queried by agents before grepping.

**Graph Stats**:
- **Nodes**: 63 (concepts, agents, capabilities, infrastructure)
- **Edges**: 54 (91% EXTRACTED, 9% INFERRED)
- **Communities**: 13 labeled
  - Procurement Domain Model, Agent Architecture, Application UX & UI, Knowledge Graph & Evidence, Vendor Intelligence, Comparison Engine, Decision Support, Data & Artifacts, Sprint 1 Delivery, Databricks Infrastructure, Development & Governance, Core Capabilities, Flask & Tech Stack

**Exports**:
- `graph.json` (59 KB) — raw data
- `graph.html` (61 KB) — interactive visualization
- `GRAPH_REPORT.md` (6.5 KB) — god nodes, surprising connections, suggested questions
- `.graphify_labels.json` (0.4 KB) — community labels
- `manifest.json` (4.5 KB) — file tracking
- `cost.json` (0.2 KB) — token usage

**God Nodes** (most connected):
1. Knowledge Graph Building (5 edges)
2. Purchase Project (4 edges)
3. Procure AI Workspace (3 edges)
4. Vendor Comparison (3 edges)
5. Comparison Intelligence (3 edges)

---

### 3. opencode.json (Repo Root)
Project configuration for OpenCode/Cursor integration.

**Contents**:
- **Personae**: senior-frontend-developer, senior-backend-developer
- **Skills**: Flask, LangChain, LangGraph, Databricks (apps, core, UC), Python best practices, React
- **MCP**: Graphify (for knowledge graph queries)
- **Environment**: Python ≥3.11, uv, .venv/
- **Conventions**: conventional commits, snake_case Python, camelCase TS/JS, Google-style docstrings, pytest
- **Knowledge Base**: `.design_docs/assistent/` with graphify-out/ graph
- **Sprint 1**: 12 deliverables, Flask + LangChain + Databricks

---

### 4. .opencode/ Control Plane
Project-specific agent workspace.

**Structure**:
```
.opencode/
  ├── QUICKSTART.md          ← Start here (10 sections, agent orientation)
  ├── SETUP_SUMMARY.md       ← This file
  ├── skills/
  │   └── README.md          ← Imported skills + custom skill template
  ├── mcps/
  │   └── graphify.md        ← Graphify MCP config (god nodes, quick start)
  └── handoffs/
      └── README.md          ← Handoff template (status, next, blockers, git state, task link)
```

All files are tracked in git. Used for inter-agent communication and project-specific guidance.

---

## What an Agent Sees on First Run

1. **OpenCode discovers** `opencode.json` → loads personae, skills, MCP
2. **Agent reads** `AGENTS.md` (instructions auto-loaded)
3. **Agent reads** `.opencode/QUICKSTART.md` for orientation
4. **Agent queries** graphify for architecture questions before writing code
5. **Agent creates** task plan in `.design_docs/assistent/tasks/` (not yet shown)
6. **Agent works** from `.design_docs/assistent/` as control plane
7. **Agent writes** app code in `web_app/` or appropriate location
8. **Agent handoffs** via `.opencode/handoffs/` + git commit

---

## Quick Agent Checklist

- [ ] Read AGENTS.md (2 min)
- [ ] Read .opencode/QUICKSTART.md (5 min)
- [ ] Run `graphify query "question"` from `.design_docs/assistent/` (1 min)
- [ ] Check `.design_docs/Knowledge/` for domain context (as needed)
- [ ] Create task plan in `.design_docs/assistent/tasks/task_<sprint>_<feature>.md`
- [ ] Build code (Flask, agents, etc.)
- [ ] Commit with conventional commits (`feat(scope):`, `fix:`, `docs:`, `chore:`)
- [ ] Handoff: `.opencode/handoffs/handoff_<task>.md` + push

---

## Files NOT Modified (Protected)

- ✅ `.design_docs/Knowledge/` — never edit (agent read-only enforcement in AGENTS.md)
- ✅ `.design_docs/Map.md` — defines folder model, do not change
- ✅ `.design_docs/.obsidian/` — Obsidian config (tracked but don't scan in builds)

---

## Next Steps for Sprint 1

From README.md:143 — 12 deliverables in order:

1. **Deploy Databricks App** — Use `ai-saas`, not `procure-ai-workspace`
2. **Flask App** — Core framework + blueprint structure
3. **User Table** — Model & persistence (Lakebase or UC)
4. **X-Forwarded Header Handling** — Extract SSO headers from Databricks Apps
5. **Telemetry** — Logging & metrics
6. **Chat Agent** — Conversational core (LangChain/LangGraph)
7. **Model Registry** — LLM endpoint config (Databricks or external)
8. **Context Management** — Memory buffer, token budget, history
9. **User Tools & MCP** — SharePoint, Outlook, OneDrive, user memory
10. **HITL** — Human-in-the-loop approval & clarifications
11. **Session Management** — Multi-turn persistence
12. **Templates** — Prompt templates & artifact schemas

See README.md:143 and `.design_docs/Knowledge/` for detailed requirements.

---

## Graph Queries (Common Patterns)

```powershell
cd .design_docs/assistent

# Architecture questions
graphify query "how do requirements flow to vendors?"
graphify query "what agents interact with the knowledge graph?"

# Node explanation
graphify explain "Purchase Project"
graphify explain "Agent Architecture"

# Path finding
graphify path "Purchase Project" "Comparison Matrix"
graphify path "Intake Agent" "Comparison Engine"

# Custom questions
graphify query "what are the 5 stages of the procurement workflow?"
```

All queries use node labels (human-readable) — graphify translates to IDs internally.

---

## Contact / Issues

- **Architecture questions**: `/graphify query` or read `.design_docs/Knowledge/`
- **Command reference**: `.design_docs/assistent/setup_details.md` (full uv, git, Flask, Databricks)
- **Governance**: `AGENTS.md` Section 1 (folder model, read-only rules)
- **Current task status**: `.opencode/handoffs/` (from previous agent)
- **Project config**: `opencode.json` (personae, skills, MCP)

---

## Cleanup Performed

- ✅ Removed `.obsidian/` artifacts from graphify corpus (minified vendor JS ~6.8 MB)
- ✅ Excluded empty .md files (3 files with 0 bytes)
- ✅ Filtered to 23 relevant files (21 docs + 2 code files: pyproject.toml, README.md)
- ✅ Removed stray `graphify-out/` at repo root (graph lives only in `.design_docs/assistent/`)
- ✅ Updated .gitignore to ignore IDE temp and scratch dirs

---

## Verification

All components verified working:

- ✅ AGENTS.md — 278 lines, covers all 9 sections
- ✅ opencode.json — valid JSON, all 6 personae/skill declarations
- ✅ .opencode/ structure — all 4 directories + 4 README/guide files
- ✅ Knowledge graph — 63 nodes, 54 edges, 13 communities, HTML/JSON/MD exports
- ✅ Graphify caching — extraction cached, fast re-query
- ✅ Git history — 8 commits, clean state, remote tracked

---

## Final State

```
procure-ai-workspace/
├── AGENTS.md                              ← Instruction file (read first)
├── opencode.json                          ← Project config
├── README.md                              ← Product vision
├── pyproject.toml                         ← Python 3.11+, empty deps
├── .opencode/                             ← Agent control plane
│   ├── QUICKSTART.md
│   ├── SETUP_SUMMARY.md
│   ├── skills/README.md
│   ├── mcps/graphify.md
│   └── handoffs/README.md
├── .design_docs/
│   ├── Knowledge/                         (READ-ONLY)
│   │   ├── 00 Usecase.md
│   │   ├── 04 Agent System Arch.md
│   │   └── ... (21 files)
│   ├── Map.md                             (Folder model)
│   └── assistent/                         (READ/WRITE)
│       ├── setup_details.md
│       ├── tasks/                         (agent task plans)
│       ├── handoffs/                      (inter-agent notes)
│       ├── graphify-out/                  (knowledge graph)
│       │   ├── graph.json
│       │   ├── graph.html
│       │   ├── GRAPH_REPORT.md
│       │   └── ...
│       └── scratch/                       (temp debug logs)
├── web_app/                               (EMPTY — greenfield Sprint 1)
└── .git/                                  (tracked: AGENTS.md, opencode.json, .opencode/, graph)
```

**Next agent**: Start with `.opencode/QUICKSTART.md` and `AGENTS.md`.

🚀 **Ready for development.**
