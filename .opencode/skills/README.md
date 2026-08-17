# Project Skills — Custom & Imported

This directory holds or references skills specific to this project.

## Imported Skills (from note.md)

### Backend & Web
- **Flask**: `D:\Work\Etex\Business Usecase\Procurement Solutions\00_Vendor_Comparison\components\PDF Parser\.agents\skills\flask-python\SKILL.md`
- **Jinja2**: `D:\Work\Etex\Business Usecase\Procurement Solutions\00_Vendor_Comparison\components\PDF Parser\.agents\skills\jinja2\SKILL.md`
- **FastAPI** (reference): `https://github.com/fastapi/fastapi/blob/master/fastapi/.agents/skills/fastapi/SKILL.md`

### Frontend
- **TypeScript**: `D:\Work\Etex\Business Usecase\Procurement Solutions\00_Vendor_Comparison\components\PDF Parser\.agents\skills\typescript-best-practices\SKILL.md`
- **JavaScript**: `D:\Work\Etex\Business Usecase\Procurement Solutions\00_Vendor_Comparison\components\PDF Parser\.agents\skills\javascript\SKILL.md`

### AI & Data
- **Databricks Skills**: `https://github.com/databricks/databricks-agent-skills`
- **LangChain MCP**: `https://docs.langchain.com/use-these-docs`
- **MLflow Skills**: `https://github.com/mlflow/skills`

## Built-in OpenCode Skills Used

Declared in `opencode.json`:
- `flask-api` — Flask REST APIs, Jinja2, blueprints
- `langchain-expert` — LangChain chains, tools, RAG
- `langgraph-architect` — Multi-agent design
- `databricks-apps-python` — Databricks Apps backend
- `databricks-core` — Databricks CLI, auth, bundles
- `databricks-unity-catalog` — UC governance
- `python-best-practices` — Python 3.11+, uv, testing
- `react-component` — React (if FE framework chosen)

## Custom Skills (if needed)

If you create project-specific skills, add them here and reference them in `opencode.json`.

Example:
```json
{
  "name": "procure-ai-domain",
  "path": ".opencode/skills/procure_ai_domain.md",
  "description": "Procurement domain concepts, vendor comparison logic, HITL patterns"
}
```

## Loading a Skill in OpenCode

```
/load flask-api
/load langchain-expert
/load procure-ai-domain
```

Or import in AGENTS.md via the `instructions` field.
