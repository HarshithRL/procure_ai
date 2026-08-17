# Graph Report - D:\Work\Etex\Procure_AI_Workspace  (2026-08-18)

## Corpus Check
- 23 files · ~19,857 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 63 nodes · 54 edges · 13 communities (12 shown, 1 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Procurement Domain Model
- Agent Architecture
- Application UX & UI
- Knowledge Graph & Evidence
- Vendor Intelligence
- Comparison Engine
- Decision Support
- Data & Artifacts
- Sprint 1 Delivery
- Databricks Infrastructure
- Development & Governance
- Flask & Tech Stack

## God Nodes (most connected - your core abstractions)
1. `Knowledge Graph Building` - 5 edges
2. `Purchase Project` - 4 edges
3. `Procure AI Workspace` - 3 edges
4. `Vendor Comparison` - 3 edges
5. `Comparison Intelligence` - 3 edges
6. `Evaluation Agent` - 3 edges
7. `Prepare Stage` - 3 edges
8. `Decide Stage` - 3 edges
9. `Comparison Matrix` - 2 edges
10. `Requirement Intelligence` - 2 edges

## Surprising Connections (you probably didn't know these)
- `Purchase Knowledge Graph` --semantically_similar_to--> `Knowledge Graph Building`  [INFERRED] [semantically similar]
  .design_docs/Knowledge/01 End-to-End Flow.md → .design_docs/Knowledge/02 Core Product Capability.md
- `Procure AI Workspace` --cites--> `Procure AI Workspace Project`  [EXTRACTED]
  .design_docs/Knowledge/00 Usecase.md → README.md
- `Artifact Agent` --semantically_similar_to--> `Artifact Generation`  [INFERRED] [semantically similar]
  .design_docs/Knowledge/04 Agent System Arch.md → .design_docs/Knowledge/02 Core Product Capability.md
- `Decide Stage` --semantically_similar_to--> `Decision Brief`  [INFERRED] [semantically similar]
  .design_docs/Knowledge/05.01 Flow Version 1.0v - design principle.md → .design_docs/Knowledge/05.1 Application View.md
- `Procure AI Workspace Project` --conceptually_related_to--> `Databricks App Deployment`  [EXTRACTED]
  README.md → .design_docs/assistent/setup_details.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Procurement Workflow** — design_docs_knowledge_05_01_flow_understand_stage, design_docs_knowledge_05_01_flow_prepare_stage, design_docs_knowledge_05_01_flow_compare_stage, design_docs_knowledge_05_01_flow_decide_stage, design_docs_knowledge_05_01_flow_deliver_stage [EXTRACTED 1.00]
- **Agent Knowledge Processing Chain** — design_docs_knowledge_04_agent_system_arch_intake_agent, design_docs_knowledge_04_agent_system_arch_document_intelligence_agent, design_docs_knowledge_04_agent_system_arch_vendor_intelligence_agent, design_docs_knowledge_04_agent_system_arch_evidence_agent, design_docs_knowledge_04_agent_system_arch_knowledge_builder [EXTRACTED 1.00]
- **Agent Decision Intelligence Chain** — design_docs_knowledge_04_agent_system_arch_evaluation_agent, design_docs_knowledge_04_agent_system_arch_comparison_agent, design_docs_knowledge_04_agent_system_arch_risk_agent, design_docs_knowledge_04_agent_system_arch_decision_intelligence_agent [EXTRACTED 1.00]
- **Core Capabilities Stack** — design_docs_knowledge_02_core_product_document_intelligence, design_docs_knowledge_02_core_product_requirement_intelligence, design_docs_knowledge_02_core_product_vendor_intelligence, design_docs_knowledge_02_core_product_comparison_intelligence, design_docs_knowledge_02_core_product_decision_intelligence [EXTRACTED 1.00]

## Communities (13 total, 1 thin omitted)

### Community 0 - "Procurement Domain Model"
Cohesion: 0.20
Nodes (10): Databricks App Deployment, Flask Application Framework, Git Version Control Workflow, UV Package Manager, AI Assistant, Direct Purchase, Indirect Purchase, Procure AI Workspace (+2 more)

### Community 1 - "Agent Architecture"
Cohesion: 0.29
Nodes (8): Purchase Knowledge Graph, Comparison Intelligence, Decision Intelligence, Document Intelligence, Evidence Graph, Knowledge Graph Building, Requirement Intelligence, Vendor Intelligence

### Community 2 - "Application UX & UI"
Cohesion: 0.29
Nodes (7): Compare Stage, Decide Stage, Deliver Stage, Prepare Stage, Purchase Readiness, Understand Stage, Decision Brief

### Community 3 - "Knowledge Graph & Evidence"
Cohesion: 0.33
Nodes (6): Comparison Agent, Decision Intelligence Agent, Deterministic Scoring Engine, Evaluation Agent, Human-in-the-Loop, Risk Agent

### Community 4 - "Vendor Intelligence"
Cohesion: 0.40
Nodes (5): Comparison Matrix, PPT Presentation, Vendor Comparison, Artifact Generation, Artifact Agent

### Community 5 - "Comparison Engine"
Cohesion: 0.40
Nodes (5): Agent Layer, Hybrid Knowledge Architecture, Purchase Orchestrator, Procurement Controller, Purchase Intelligence Model

### Community 6 - "Decision Support"
Cohesion: 0.40
Nodes (5): Entity & Fact Extraction, HITL Knowledge Acquisition, Knowledge Normalization, Knowledge Validation, Relationship Extraction

### Community 7 - "Data & Artifacts"
Cohesion: 0.40
Nodes (5): Document Intelligence Agent, Evidence Agent, Intake Agent, Knowledge Builder Agent, Vendor Intelligence Agent

### Community 8 - "Sprint 1 Delivery"
Cohesion: 0.50
Nodes (4): Commercial Normalization, Red Flag Knowledge, Etex Direct Comparison, Etex Indirect / IT Comparison

### Community 9 - "Databricks Infrastructure"
Cohesion: 0.67
Nodes (3): Like-for-Like Comparison, Comparison Result States, Total Cost of Ownership

### Community 10 - "Development & Governance"
Cohesion: 0.67
Nodes (3): AI Copilot, Dashboard, Purchase Decision Workspace

## Knowledge Gaps
- **25 isolated node(s):** `procure-ai`, `Direct Purchase`, `Indirect Purchase`, `PPT Presentation`, `AI Assistant` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Procure AI Workspace` connect `Procurement Domain Model` to `Vendor Intelligence`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `Vendor Comparison` connect `Vendor Intelligence` to `Procurement Domain Model`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **What connects `procure-ai`, `Direct Purchase`, `Indirect Purchase` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._