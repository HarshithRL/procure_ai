# .opencode/ — Agent Control Plane Index

**Navigation guide for the Procure AI agent workspace.**

---

## 📖 Start Here (Read in Order)

1. **`../AGENTS.md`** (repo root) — 5 min read
   - Workspace governance, tech stack, constraints
   - Read-only rules (Knowledge/) and read-write rules (assistent/)
   - Knowledge graph location and usage
   - Sprint 1 deliverables checklist
   - Full command reference

2. **`QUICKSTART.md`** (this directory) — 5 min read
   - 10-point orientation for agents
   - Common commands, folder model, tech stack overview
   - Quick checklist for first task

3. **`INSTALLED_SKILLS.md`** (this directory) — 3 min scan
   - Status of all personae & skills from note.md
   - What's installed locally vs. referenced remotely
   - How to load and use each skill

4. **`LANGCHAIN_MCP_GUIDE.md`** (this directory) — 5 min read
   - LangChain MCP integration (docs-langchain + reference-langchain)
   - How to query LangChain docs from your IDE
   - Sprint 1 integration examples
   - Troubleshooting MCPs

---

## 📁 Control Plane Structure

```
.opencode/
├── INDEX.md                    ← You are here
├── QUICKSTART.md               ← Agent orientation (read #2)
├── SETUP_SUMMARY.md            ← What was set up, verification
├── INSTALLED_SKILLS.md         ← Skill inventory & installation status
│
├── skills/
│   └── README.md               ← References to local & remote skills
│
├── mcps/
│   ├── graphify.md             ← Knowledge graph MCP config
│   └── langchain.md            ← LangChain docs & reference MCP config
│
└── handoffs/
    └── README.md               ← Template & format for inter-agent handoffs
```

---

## 🎯 Key Files & Locations

### Instructions & Config
- `AGENTS.md` — Central agent instruction file (read-only enforcement, tech stack, governance)
- `opencode.json` — Project configuration (personae, skills, MCP, environment)
- `README.md` (repo root) — Product vision & Sprint 1 deliverables

### Knowledge Base
- `.design_docs/Knowledge/` — Source of truth (READ-ONLY)
  - 21 design documents, 0 bytes of code
  - Cover: domain model, agent arch, UX design, infrastructure, governance
  - Never edit these files

- `.design_docs/assistent/` — Read/Write control plane
  - `setup_details.md` — Master command reference (uv, git, Flask, Databricks)
  - `tasks/` — Agent task plans (create `task_sprint1_<feature>.md`)
  - `handoffs/` — Inter-agent status notes
  - `graphify-out/` — Knowledge graph (63 nodes, 54 edges, 13 communities)
  - `scratch/` — Temporary debug logs

### Application Code (Greenfield)
- `web_app/` — Empty (Sprint 1 will add Flask app here)
- `pyproject.toml` — Python ≥3.11, empty dependencies (use `uv add`)
- `requirements.txt` — Managed via `uv`, not hand-edited

---

## 🔧 Personae & Skills

### Personae (2)
- `senior-frontend-developer` — UI architecture, HTMX/Jinja/Alpine/Tailwind, web vitals, a11y
- `senior-backend-developer` — API design, FastAPI/LangGraph/Python, databases, system design

**Load in chat**:
```
/load senior-backend-developer
"Design the agent architecture for Sprint 1 chat intake"
```

### Skills (15 total)

**Built-in OpenCode** (always available):
1. `flask-api` — Flask REST APIs, blueprints, Jinja2 templates
2. `langchain-expert` — LangChain chains, tools, RAG
3. `langgraph-architect` — Multi-agent design from requirements
4. `databricks-apps-python` — Python backend for Databricks Apps
5. `databricks-core` — CLI, auth, profiles, bundles
6. `databricks-unity-catalog` — UC governance & access control
7. `python-best-practices` — Python 3.11+, uv, pytest, linting, types
8. `react-component` — React (if FE framework chosen later)

**Local** (from PDF Parser .agents/):
9. `typescript-best-practices` — TS patterns, generics, type safety
10. `flask-python` — Flask patterns & best practices
11. `javascript` — JS fundamentals, async, DOM
12. `jinja2` — Jinja2 templating, inheritance, forms

**Remote** (documented, not installed):
13. `fastapi` (github.com/fastapi/...) — FastAPI framework
14. Databricks agent skills (github.com/databricks/databricks-agent-skills)
15. MLflow skills (github.com/mlflow/skills)

**Load in chat**:
```
/load flask-api
/load langchain-expert
```

---

## 📊 Knowledge Graph

**Location**: `.design_docs/assistent/graphify-out/`

**Stats**:
- 63 nodes (concepts, agents, capabilities)
- 54 edges (relationships, dependencies)
- 13 communities (labeled by domain)

**Exports**:
- `graph.json` — Raw data
- `graph.html` — Interactive visualization (open in browser)
- `GRAPH_REPORT.md` — Audit, god nodes, surprising connections

**Use from `.design_docs/assistent/`**:
```powershell
graphify query "how do requirements flow to vendors?"
graphify explain "Purchase Project"
graphify path "Intake Agent" "Comparison Engine"
```

---

## ✅ Installation Verification

**From note.md**:
- ✅ Personae: 2/2 installed (senior FE, senior BE)
- ✅ Local skills: 4/4 installed (TypeScript, Flask, JS, Jinja2)
- ✅ Built-in skills: 8/8 available (Flask, LangChain, Databricks, Python, React)
- ⚠️ Remote references: 4/4 documented (not installed, but referenced)

**All requirements from note.md satisfied.**

---

## 🚀 First Task Checklist

Before starting development:

- [ ] Read `AGENTS.md` (section 1 governance, section 4 tech stack)
- [ ] Read `QUICKSTART.md` (this directory)
- [ ] Run `/graphify query` from `.design_docs/assistent/`
- [ ] Load a persona: `/load senior-backend-developer`
- [ ] Create task plan: `.design_docs/assistent/tasks/task_sprint1_<feature>.md`
- [ ] Start coding in `web_app/` or appropriate location
- [ ] Commit with conventional commits: `feat(scope):`, `fix:`, `docs:`, `chore:`
- [ ] Handoff: `.opencode/handoffs/handoff_<task>.md` + push

---

## 📝 Common Patterns

### Loading a Skill
```
/load flask-api
"Help me design the Flask app structure"
```

### Querying the Graph
```
cd .design_docs/assistent
graphify query "what are the agent responsibilities?"
graphify explain "Vendor Comparison"
```

### Querying LangChain MCP
```
# From your agent/IDE, query LangChain documentation directly
docs-langchain:
"How do I build a multi-agent system with LangChain?"

reference-langchain:
"What are the parameters for ChatOpenAI class?"
```

See `LANGCHAIN_MCP_GUIDE.md` for full examples.

### Creating a Task Plan
Create `.design_docs/assistent/tasks/task_sprint1_flask_app.md`:
```markdown
# Sprint 1: Flask App Setup

**Deliverable**: Core Flask app with blueprint structure, /api/profile endpoint

**Requirements**: 
- From AGENTS.md Section 6: deliverable #2, #4 (SSO headers), #5 (telemetry)
- Read: .design_docs/Knowledge/04 Agent System Arch.md

**Implementation Plan**:
1. Flask app factory pattern
2. Blueprints for /api, /auth, /chat
3. X-Forwarded header extraction middleware
4. Basic telemetry logging
5. Test with curl + Databricks headers

**Blockers**: None
**Git branch**: feature/sprint1-flask-app
```

### Handing Off
Create `.opencode/handoffs/handoff_flask_app.md`:
```markdown
# Handoff: Flask App Setup Complete

**Status**: Flask app scaffolded, blueprints created, 3 endpoints working

**Next Steps**:
1. Implement user table (Lakebase or UC)
2. Wire up chat agent integration
3. Add session management

**Blockers**: None

**Git State**: Branch feature/sprint1-flask-app, ready to merge

**Task Plan**: .design_docs/assistent/tasks/task_sprint1_flask_app.md
```

---

## 🔗 Quick Links

| File | Purpose | Read Time |
|------|---------|-----------|
| `../AGENTS.md` | Central instructions | 5 min |
| `QUICKSTART.md` | Agent orientation | 5 min |
| `INSTALLED_SKILLS.md` | Skill inventory | 3 min |
| `SETUP_SUMMARY.md` | What was set up | 5 min |
| `../README.md` | Product vision | 10 min |
| `.design_docs/assistent/setup_details.md` | Commands reference | 10 min (scan) |
| `.design_docs/assistent/graphify-out/GRAPH_REPORT.md` | Graph audit | 10 min |

---

## ❓ FAQ

**Q: Where do I write application code?**  
A: `web_app/` (currently empty). Sprint 1 creates Flask app here.

**Q: Can I edit `.design_docs/Knowledge/`?**  
A: NO. It's READ-ONLY. Design decisions are owned by the project owner. You can *read* it.

**Q: How do I query the knowledge graph?**  
A: From `.design_docs/assistent/`, run: `graphify query "your question"`

**Q: Where do I create my task plan?**  
A: `.design_docs/assistent/tasks/task_sprint1_<feature>.md`

**Q: How do I handoff to the next agent?**  
A: Create `.opencode/handoffs/handoff_<task>.md` with status, next steps, blockers, git state, and task plan link.

**Q: What if I need a skill that's not installed?**  
A: Check `INSTALLED_SKILLS.md`. If remote, download to `.opencode/skills/<name>/` and add to `opencode.json`.

**Q: Where's the command reference?**  
A: `.design_docs/assistent/setup_details.md` (sections 2-4 cover uv, UI, git, Databricks)

---

## 🎓 Reading Order for First Agent

1. **This file** (2 min) — You're building context
2. `../AGENTS.md` Section 1-3 (8 min) — Governance & tech stack
3. `QUICKSTART.md` (5 min) — Orientation
4. `.design_docs/Knowledge/04 Agent System Arch.md` (20 min) — Agent design
5. `../README.md` (10 min) — Product goal
6. `.design_docs/assistent/setup_details.md` (scan sections 2-4, 5 min) — Commands
7. Start coding (create task plan first)

**Total prep time**: ~1 hour for full context.

---

**Welcome to Procure AI. Start with QUICKSTART.md. Ask the graph before grepping. Build with confidence.** 🚀
