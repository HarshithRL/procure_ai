# Graphify MCP Configuration

## Location
Knowledge graph built at: `.design_docs/assistent/graphify-out/`

## Quick Start

```powershell
# From .design_docs/assistent/, query the graph
cd .design_docs/assistent
graphify query "how do requirements flow to vendors?"
graphify explain "Vendor Comparison"
graphify path "Purchase Project" "Comparison Matrix"
```

## Graph Stats
- **Nodes**: 63 (concepts, agents, capabilities, infrastructure)
- **Edges**: 54 (relationships, dependencies)
- **Communities**: 13 (labeled by domain area)
  - Procurement Domain Model
  - Agent Architecture
  - Application UX & UI
  - Knowledge Graph & Evidence
  - Vendor Intelligence
  - Comparison Engine
  - Decision Support
  - Databricks Infrastructure
  - Development & Governance
  - Flask & Tech Stack

## Key God Nodes (most connected)
1. Knowledge Graph Building (5 edges)
2. Purchase Project (4 edges)
3. Procure AI Workspace (3 edges)
4. Vendor Comparison (3 edges)
5. Comparison Intelligence (3 edges)

## Node ID Format
Every node uses the deterministic format:
```
{repo-relative-path}_{entity}
```
Examples:
- `design_docs_knowledge_04_agent_system_arch_langchain_agent`
- `design_docs_assistent_setup_details_databricks_app_deployment`
- `readme_ai_powered_procurement`

Lowercase, `[a-z0-9_]` only. Non-alphanumerics → `_`.

## Graph Exports
- `graph.json` — raw graph data
- `graph.html` — interactive visualization (open in browser)
- `GRAPH_REPORT.md` — audit, god nodes, surprising connections
- `.graphify_labels.json` — community names
- `manifest.json` — file tracking for incremental updates
- `cost.json` — token usage history

## Updates
To re-extract after design docs change:
```powershell
cd .design_docs/assistent
graphify --update
```

This only re-extracts changed files (cached extraction preserved).

## When to Use
- Before grepping or searching design docs
- Architecture/relationship questions ("what connects X to Y?")
- Understanding agent dependencies or UX flows
- Cross-cutting concerns (governance, infrastructure)

Do NOT use for: implementation details, code navigation (use grep/Glob), or line-by-line code review.
