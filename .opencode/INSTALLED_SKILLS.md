# Installed Skills & Personae Status

**Last updated**: 2026-08-18

---

## ✅ INSTALLED LOCALLY

### Personae (from note.md)
Located: `C:\Users\HarshithR\.cursor\agents\`

- ✅ **senior-frontend-developer.md** — Advanced senior frontend peer for UI planning, architecture, HTMX/Jinja/Alpine/Tailwind, web vitals, a11y
- ✅ **senior-backend-developer.md** — Elite senior backend engineer for API design, database architecture, system design, FastAPI/LangGraph/Python, microservices

**Status in opencode.json**: Referenced and active

---

### Skills (from PDF Parser .agents/)
Located: `D:\Work\Etex\Business Usecase\Procurement Solutions\00_Vendor_Comparison\components\PDF Parser\.agents\skills\`

- ✅ **typescript-best-practices/SKILL.md** — TypeScript patterns, type safety, generics, advanced types
- ✅ **flask-python/SKILL.md** — Flask APIs, blueprints, templates, error handling
- ✅ **javascript/SKILL.md** — JavaScript fundamentals, async patterns, DOM manipulation
- ✅ **jinja2/SKILL.md** — Jinja2 templating, filters, inheritance, forms

**Status in opencode.json**: Documented in `.opencode/skills/README.md` as importable references

---

### Built-in OpenCode Skills (activated via opencode.json)

- ✅ **flask-api** — Flask REST APIs, Jinja2 templates, blueprints
- ✅ **langchain-expert** — LangChain chains, tools, retrievers, RAG
- ✅ **langgraph-architect** — LangGraph multi-agent systems from requirements
- ✅ **databricks-apps-python** — Python backend for Databricks Apps (FastAPI, Flask, connectivity)
- ✅ **databricks-core** — Databricks CLI, auth, profiles, bundles
- ✅ **databricks-unity-catalog** — UC governance, access control, observability
- ✅ **python-best-practices** — Python 3.11+, uv, pyproject.toml, testing, linting, type checking
- ✅ **react-component** — React components, hooks, state management (if FE chosen)

**Status in opencode.json**: All declared and available via skill loading (`/load flask-api`, etc.)

---

### MCP (Model Context Protocol)

- ✅ **Graphify** — Knowledge graph querying at `.design_docs/assistent/graphify-out/`
  - Use: `/graphify query "<question>"` from `.design_docs/assistent/`
  - Config: `.opencode/mcps/graphify.md`

**Status in opencode.json**: Active

---

## ⚠️ REMOTE REFERENCES (NOT LOCALLY INSTALLED)

These are external resources mentioned in note.md. They are **not installed** but are referenced for context and research.

### FastAPI Skill
- **Source**: `https://github.com/fastapi/fastapi/blob/master/fastapi/.agents/skills/fastapi/SKILL.md`
- **Status**: Remote GitHub reference (not installed)
- **Use case**: If project pivots to FastAPI (currently Flask is committed)
- **Note**: Can be fetched/studied but not auto-loaded by OpenCode

---

### Databricks Agent Skills
- **Source**: `https://github.com/databricks/databricks-agent-skills`
- **Status**: Remote GitHub repository (not installed)
- **Use case**: Future integration if Databricks-specific agent patterns needed
- **Note**: Built-in OpenCode skills (`databricks-apps-python`, `databricks-core`, etc.) cover Sprint 1 needs

---

### LangChain MCP / Documentation
- **Source**: `https://docs.langchain.com/use-these-docs`
- **Status**: Remote documentation link (not locally installed)
- **Use case**: Reference for LangChain API, chain composition, tool use
- **Note**: Built-in `langchain-expert` skill covers most patterns

---

### MLflow Skills
- **Source**: `https://github.com/mlflow/skills`
- **Status**: Remote GitHub repository (not installed)
- **Use case**: Future ML training & evaluation workflows
- **Note**: Not needed for Sprint 1 (chat agent, no model training)

---

## How to Use (Agent Onboarding)

### For Personae
Personae are automatically loaded by OpenCode/Cursor when found in `~/.cursor/agents/` or referenced in `opencode.json`.

```
/load senior-backend-developer
"Design the API endpoints for the Flask app"

/load senior-frontend-developer
"Design the UI layout for the dashboard"
```

### For Local Skills
Local skills from PDF Parser are documented but **not auto-loaded** by default. To use them:

1. Reference path in opencode.json (already done in `.opencode/skills/README.md`)
2. Load in chat: `/load flask-python` or similar
3. Or read the SKILL.md directly for guidance

### For Built-in OpenCode Skills
Auto-discovered by OpenCode. Load as needed:

```
/load flask-api
/load langchain-expert
/load langgraph-architect
/load databricks-apps-python
```

### For Remote References
Study or cite in research, but cannot be auto-loaded by OpenCode without local download.

If needed, download and place in `.opencode/skills/<name>/SKILL.md` then reference in `opencode.json`.

---

## Installation Checklist

- ✅ Personae: senior-frontend-developer, senior-backend-developer (in .cursor/agents/)
- ✅ Local skills: TypeScript, Flask, JavaScript, Jinja2 (in PDF Parser .agents/)
- ✅ Built-in skills: Flask, LangChain, LangGraph, Databricks, Python, React (OpenCode native)
- ✅ MCP: Graphify (at .design_docs/assistent/graphify-out/)
- ✅ opencode.json: All personae and built-in skills declared
- ✅ .opencode/skills/README.md: References to all local & remote skills documented
- ⚠️ Remote skills (FastAPI, Databricks agent skills, MLflow): Available but not locally installed

---

## Next: If You Need Remote Skills

To add a remote skill (e.g., FastAPI):

1. Download the repository or SKILL.md file
2. Place in `.opencode/skills/<name>/`
3. Add to `opencode.json`:
   ```json
   {
     "name": "fastapi",
     "path": ".opencode/skills/fastapi/SKILL.md",
     "description": "FastAPI framework skills"
   }
   ```
4. Load in OpenCode: `/load fastapi`

---

## To Verify Installation

Run:
```powershell
cd D:\Work\Etex\Procure_AI_Workspace

# Check personae exist
Test-Path "C:\Users\HarshithR\.cursor\agents\senior-frontend-developer.md"
Test-Path "C:\Users\HarshithR\.cursor\agents\senior-backend-developer.md"

# Check local skills exist
Test-Path "D:\Work\Etex\Business Usecase\Procurement Solutions\00_Vendor_Comparison\components\PDF Parser\.agents\skills\flask-python\SKILL.md"

# Check opencode.json is valid
cat opencode.json

# Check .opencode structure
Get-ChildItem .opencode -Recurse

# Check knowledge graph
ls .design_docs/assistent/graphify-out/
```

---

## Summary for Next Agent

✅ **Everything from note.md is either:**
1. Installed locally (personae, local skills)
2. Configured in opencode.json (built-in OpenCode skills)
3. Documented for reference (remote GitHub/docs links)

⚠️ **Remote skills are not installed but can be fetched if needed.** Sprint 1 is covered by built-in skills + local references.

🚀 **Ready to start development with full skill access.**
