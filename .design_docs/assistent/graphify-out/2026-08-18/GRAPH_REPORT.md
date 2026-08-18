# Graph Report - assistent  (2026-08-18)

## Corpus Check
- 9 files · ~11,389 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 246 nodes · 238 edges · 11 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9264d78b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ✅ Databricks App Deployment Setup — COMPLETE
- Databricks App Deployment Setup — Complete Reference
- LangChain MCP Setup Complete
- Databricks App Deployment Verification Guide
- 4. Master Git Version Control Reference
- Sprint 1 Deployment Task — Databricks App Setup
- Project Status — Procure AI Workspace
- Handoff: Sprint 1 Databricks App Deployment Setup
- Databricks App Deployment — Quick Checklist
- 2.2 Package Management & Dependencies
- Who Can Use It

## God Nodes (most connected - your core abstractions)
1. `✅ Databricks App Deployment Setup — COMPLETE` - 15 edges
2. `Databricks App Deployment Setup — Complete Reference` - 13 edges
3. `LangChain MCP Setup Complete` - 13 edges
4. `Project Status — Procure AI Workspace` - 13 edges
5. `4. Master Git Version Control Reference` - 11 edges
6. `Databricks App Deployment — Quick Checklist` - 10 edges
7. `Databricks App Deployment Verification Guide` - 10 edges
8. `Handoff: Sprint 1 Databricks App Deployment Setup` - 10 edges
9. `Sprint 1 Deployment Task — Databricks App Setup` - 10 edges
10. `Who Can Use It` - 7 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Communities (11 total, 0 thin omitted)

### Community 0 - "✅ Databricks App Deployment Setup — COMPLETE"
Cohesion: 0.06
Nodes (34): 1. Exclude Patterns in DAB Bundle, 1. Validation Phase, 2. Database Strategy (Sprint 1), 2. Deployment Phase, 3. Configuration Structure, 3. Startup Phase, 4. Verification Phase, 🔧 Configuration Files Created (+26 more)

### Community 1 - "Databricks App Deployment Setup — Complete Reference"
Cohesion: 0.06
Nodes (33): 1. Bundle Structure, 2. Exclusion Pattern Matching, 3. App Startup, Authentication, Common Issues, Configuration Files Created, DAB Configuration Files, Database Behavior (+25 more)

### Community 2 - "LangChain MCP Setup Complete"
Cohesion: 0.06
Nodes (30): ✅ All Systems Operational, Architecture, Bottom Line, Documentation & Guides, Documentation Structure, Example Sprint 1 Tasks, File Changes Summary, For Claude Code (Works Immediately) (+22 more)

### Community 3 - "Databricks App Deployment Verification Guide"
Cohesion: 0.07
Nodes (27): 1. Check App Status, 2. Stream Logs, 3. Access the App, 4. Test Endpoints, 5. Verify Seed Data, Bundle Validation Checklist, Databricks App Deployment Verification Guide, Deploy (+19 more)

### Community 4 - "4. Master Git Version Control Reference"
Cohesion: 0.08
Nodes (22): 1.1 Strict Access Rules, 1.2 Multi-Agent Workspace Organization, 1. Governance & Multi-Agent Collaboration, 3.1 Flask / Backend Development Server, 3.2 Frontend & UI Build Commands (Node / npm / Vite), 3.3 Databricks Apps & SSO Integration, 3. UI, Web App & Databricks Execution, 4.10 Releases & Tagging (+14 more)

### Community 5 - "Sprint 1 Deployment Task — Databricks App Setup"
Cohesion: 0.08
Nodes (23): 1. Created Flask Entrypoint (`app.py`), 2. Created Databricks App Config (`web_app/app.yaml`), 3. Created DAB Bundle Config (`databricks.yml`), 4. Created App Resource Definition (`resources/ai_saas.app.yml`), 5. Updated Requirements (`requirements.txt`), 6. Updated `.gitignore`, Architecture, Authentication (+15 more)

### Community 6 - "Project Status — Procure AI Workspace"
Cohesion: 0.09
Nodes (22): 1. AGENTS.md (Central Instruction File), 2. Knowledge Graph, 3. opencode.json (Project Configuration), 4. .opencode/ Control Plane (Agent Workspace), 5. Governance & Guidance, Built-in OpenCode Skills ✅, Contacts / Issues, Executive Summary (+14 more)

### Community 7 - "Handoff: Sprint 1 Databricks App Deployment Setup"
Cohesion: 0.10
Nodes (20): Common Issues & Solutions, Database Persistence (Sprint 1 vs 2), Deployment Readiness, Files Created, Files Modified, Git Status, Handoff: Sprint 1 Databricks App Deployment Setup, Important Notes (+12 more)

### Community 8 - "Databricks App Deployment — Quick Checklist"
Cohesion: 0.18
Nodes (10): After Deployment, Databricks App Deployment — Quick Checklist, Deployment (Copy/Paste These Commands), Handy References, Key Files Deployed, Key Files NOT Deployed, Post-Deployment (Verify These), Pre-Deployment (Do These First) (+2 more)

### Community 9 - "2.2 Package Management & Dependencies"
Cohesion: 0.22
Nodes (9): 2.1 Virtual Environment Setup, 2.2 Package Management & Dependencies, 2.3 Running Scripts, Tests & Tools with `uv`, 2. Python & UV Environment Management, Activate Virtual Environment, Adding & Removing Dependencies, Create & Manage Virtual Environment, Inspecting Packages (+1 more)

### Community 10 - "Who Can Use It"
Cohesion: 0.29
Nodes (7): Antigravity, Claude Code, Cursor, Deep Agents Code, OpenCode, VS Code, Who Can Use It

## Knowledge Gaps
- **184 isolated node(s):** `Overview`, `✅ Production Code (Included)`, `❌ Excluded (NOT Deployed)`, `DAB Configuration Files`, `1. Bundle Structure` (+179 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Databricks App Deployment Setup — Complete Reference` connect `Databricks App Deployment Setup — Complete Reference` to `4. Master Git Version Control Reference`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Procure AI Workspace — Setup & Command Reference` connect `4. Master Git Version Control Reference` to `2.2 Package Management & Dependencies`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `LangChain MCP Setup Complete` connect `LangChain MCP Setup Complete` to `Who Can Use It`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `Overview`, `✅ Production Code (Included)`, `❌ Excluded (NOT Deployed)` to the rest of the system?**
  _184 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `✅ Databricks App Deployment Setup — COMPLETE` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._
- **Should `Databricks App Deployment Setup — Complete Reference` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `LangChain MCP Setup Complete` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._