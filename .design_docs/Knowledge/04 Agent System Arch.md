
> **Business workflow drives orchestration; agents perform bounded intelligence; deterministic services perform computation; the Purchase Intelligence Model maintains shared state.**

# Agent System Architecture

> [!abstract] Purpose
> AI-native procurement system for Direct and Indirect purchasing.
>
> The system converts fragmented purchase information into:
> - structured procurement knowledge
> - evidence-backed vendor comparison
> - risk and trade-off analysis
> - human-approved recommendation
> - Excel comparison matrix
> - executive presentation

---

## 01 — Architecture Principle

The architecture is **not**:

> [!abstract] Purpose
`User → LLM → Answer`
>
It is:
>
`Business Process → Orchestration → Agent Intelligence → Knowledge → Decision → HITL → Business Artifact`


### Core principle

```text
Business Workflow
       ↓
Purchase State
       ↓
Procurement Controller
       ↓
Specialist Agents
       ↓
Shared Purchase Intelligence
       ↓
Decision Intelligence
       ↓
Human Approval
       ↓
Business Artifacts
````

---

# 02 — System Context

```mermaid
flowchart TD

    USER["Business User / Procurement User"]

    APP["AI Procurement Workspace"]

    ORCH["Purchase Orchestrator"]

    KNOW["Purchase Intelligence"]

    AGENTS["Procurement Agent System"]

    DATA["Enterprise Knowledge Layer"]

    ART["Business Artifacts"]

    USER --> APP
    APP --> ORCH

    ORCH --> AGENTS
    AGENTS --> KNOW
    KNOW --> DATA

    AGENTS --> ART
    ART --> APP

    APP --> USER
```

### Developer interpretation

- `AI Procurement Workspace`
    
    - UI
        
    - project workspace
        
    - chat
        
    - document viewer
        
    - comparison matrix
        
    - graph visualization
        
    - approval actions
        
- `Purchase Orchestrator`
    
    - controls workflow
        
    - manages project state
        
    - decides which agent should execute
        
    - manages HITL
        
    - validates stage transitions
        
- `Procurement Agent System`
    
    - performs domain reasoning
        
    - does not own persistent project state
        
- `Purchase Intelligence`
    
    - canonical project state
        
    - shared context between agents
        
- `Enterprise Knowledge Layer`
    
    - documents
        
    - structured data
        
    - graph
        
    - vector retrieval
        
    - evidence
        

---

# 03 — Direct vs Indirect Procurement

Direct and indirect purchasing should **not** become two independent agent systems.

```mermaid
flowchart TD

    PURCHASE["New Purchase"]

    TYPE["Purchase Type"]

    DIRECT["DIRECT PURCHASE"]
    INDIRECT["INDIRECT PURCHASE"]

    DIRECT_FLOW["Direct Procurement Workflow"]
    INDIRECT_FLOW["Indirect Procurement Workflow"]

    COMMON["Common Procurement Intelligence"]

    PURCHASE --> TYPE

    TYPE --> DIRECT
    TYPE --> INDIRECT

    DIRECT --> DIRECT_FLOW
    INDIRECT --> INDIRECT_FLOW

    DIRECT_FLOW --> COMMON
    INDIRECT_FLOW --> COMMON

    COMMON --> REQUIREMENT["Requirement Intelligence"]
    COMMON --> VENDOR["Vendor Intelligence"]
    COMMON --> EVAL["Evaluation"]
    COMMON --> COMP["Comparison"]
    COMMON --> DECISION["Decision Intelligence"]
```

### Key architecture decision

```text
Workflow = configurable

Intelligence = shared

Decision model = shared

Artifacts = shared
```

Direct and indirect procurement can therefore have different:

- intake questions
    
- required documents
    
- approval stages
    
- evaluation criteria
    
- procurement policies
    

while sharing:

- document intelligence
    
- knowledge construction
    
- evidence management
    
- vendor normalization
    
- comparison
    
- risk analysis
    
- recommendation
    
- artifact generation
    

---

# 04 — Complete Agent System

```mermaid
flowchart TD

    USER["User"]

    ORCH["PURCHASE ORCHESTRATOR"]

    CTRL["PROCUREMENT CONTROLLER"]

    subgraph UNDERSTAND["01 — UNDERSTAND"]
        INTAKE["Intake Agent"]
        REQ["Requirement Intelligence Agent"]
        CLARIFY["Clarification Agent"]
    end

    subgraph KNOWLEDGE["02 — BUILD KNOWLEDGE"]
        DOC["Document Intelligence Agent"]
        ENTITY["Entity Intelligence"]
        VENDOR["Vendor Intelligence Agent"]
        EVIDENCE["Evidence Agent"]
        KB["Knowledge Builder Agent"]
    end

    subgraph ANALYSIS["03 — ANALYZE"]
        EVAL["Evaluation Agent"]
        COMP["Comparison Agent"]
        RISK["Risk Agent"]
        SCORE["Scoring Engine"]
    end

    subgraph DECISION["04 — DECIDE"]
        DECISION_AGENT["Decision Intelligence Agent"]
        RECOMMEND["Recommendation Agent"]
    end

    subgraph DELIVERY["05 — DELIVER"]
        ARTIFACT["Artifact Agent"]
        EXCEL["Excel Generator"]
        PPT["PPT Generator"]
    end

    HITL["Human-in-the-Loop"]

    USER --> ORCH
    ORCH --> CTRL

    CTRL --> INTAKE
    INTAKE --> REQ
    REQ --> CLARIFY

    CLARIFY --> DOC
    DOC --> ENTITY
    ENTITY --> VENDOR
    VENDOR --> EVIDENCE
    EVIDENCE --> KB

    KB --> EVAL
    EVAL --> COMP
    COMP --> RISK
    RISK --> SCORE

    SCORE --> DECISION_AGENT
    DECISION_AGENT --> RECOMMEND

    RECOMMEND --> HITL

    HITL --> ARTIFACT

    ARTIFACT --> EXCEL
    ARTIFACT --> PPT
```

---

# 05 — Why These Agents Exist

|Agent|Business responsibility|Primary output|
|---|---|---|
|**Purchase Orchestrator**|Manage purchase lifecycle|workflow state|
|**Procurement Controller**|Control quality, policy and stage transitions|validated state|
|**Intake Agent**|Understand business need|purchase context|
|**Requirement Agent**|Convert business need into requirements|structured requirements|
|**Clarification Agent**|Resolve ambiguity|confirmed knowledge|
|**Document Agent**|Understand uploaded documents|structured document data|
|**Entity Intelligence**|Identify vendors, products, requirements, people, etc.|entities|
|**Vendor Agent**|Build comparable vendor profiles|vendor intelligence|
|**Evidence Agent**|Trace facts to sources|evidence|
|**Knowledge Builder**|Maintain project knowledge|knowledge graph|
|**Evaluation Agent**|Evaluate vendor against criteria|evaluation|
|**Comparison Agent**|Identify differences and trade-offs|comparison|
|**Risk Agent**|Detect commercial/technical/process risks|risk register|
|**Scoring Engine**|Calculate deterministic scores|scores|
|**Decision Agent**|Synthesize decision context|decision analysis|
|**Recommendation Agent**|Produce decision recommendation|recommendation|
|**Artifact Agent**|Convert decision model into outputs|artifacts|

---

# 06 — The Most Important Component: Purchase Intelligence

Agents should **not communicate primarily by passing huge prompts to each other**.

They should communicate through a shared structured project state.

```mermaid
flowchart TD

    PROJECT["Purchase Project"]

    CONTEXT["Purchase Context"]
    REQUIREMENTS["Requirements"]
    VENDORS["Vendor Profiles"]
    DOCUMENTS["Documents"]
    EVIDENCE["Evidence"]
    CRITERIA["Evaluation Criteria"]
    RISKS["Risks"]
    SCORES["Scores"]
    DECISIONS["Decisions"]
    ARTIFACTS["Artifacts"]

    PROJECT --> CONTEXT
    PROJECT --> REQUIREMENTS
    PROJECT --> VENDORS
    PROJECT --> DOCUMENTS
    PROJECT --> EVIDENCE
    PROJECT --> CRITERIA
    PROJECT --> RISKS
    PROJECT --> SCORES
    PROJECT --> DECISIONS
    PROJECT --> ARTIFACTS
```

Think of this as:

> **The Purchase Project is the source of truth.**

Agents operate on this state.

---

# 07 — Purchase Intelligence Model

```mermaid
flowchart LR

    PROJECT["Purchase"]

    CONTEXT["Context"]
    REQ["Requirements"]
    CRITERIA["Evaluation Criteria"]
    VENDOR["Vendors"]
    DOC["Documents"]
    EVIDENCE["Evidence"]
    CONV["Conversations"]
    ASSUMPTION["Assumptions"]
    RISK["Risks"]
    SCORE["Scores"]
    DECISION["Decision"]
    ARTIFACT["Artifacts"]

    PROJECT --> CONTEXT
    PROJECT --> REQ
    PROJECT --> CRITERIA

    REQ --> VENDOR
    VENDOR --> DOC
    DOC --> EVIDENCE

    CONV --> CONTEXT
    CONV --> ASSUMPTION

    EVIDENCE --> RISK
    EVIDENCE --> SCORE

    SCORE --> DECISION
    RISK --> DECISION

    DECISION --> ARTIFACT
```

---

# 08 — Agent vs Service Boundary

Do **not** make everything an agent.

This is important for production architecture.

```mermaid
flowchart TD

    AGENTS["AI AGENTS"]

    SERVICES["DETERMINISTIC SERVICES"]

    AGENTS --> REASONING["Reasoning"]
    AGENTS --> PLANNING["Planning"]
    AGENTS --> CLARIFICATION["Clarification"]
    AGENTS --> INTERPRETATION["Interpretation"]
    AGENTS --> DECISION["Decision Synthesis"]

    SERVICES --> PARSER["Document Parser"]
    SERVICES --> OCR["OCR"]
    SERVICES --> EXTRACT["Structured Extraction"]
    SERVICES --> SEARCH["Search / Retrieval"]
    SERVICES --> GRAPH["Graph Operations"]
    SERVICES --> SCORE["Scoring"]
    SERVICES --> VALIDATE["Validation"]
    SERVICES --> EXCEL["Excel Generation"]
    SERVICES --> PPT["PPT Generation"]
```

### Rule

> **Use an agent where reasoning or adaptive planning is required.**

> **Use a deterministic service where the operation is predictable.**

---

# 09 — Purchase Orchestrator

The orchestrator is responsible for the **workflow**, not domain reasoning.

```mermaid
stateDiagram-v2

    [*] --> CREATED

    CREATED --> INTAKE

    INTAKE --> KNOWLEDGE_BUILDING

    KNOWLEDGE_BUILDING --> REQUIREMENT_REVIEW

    REQUIREMENT_REVIEW --> VENDOR_ANALYSIS

    VENDOR_ANALYSIS --> COMPARISON

    COMPARISON --> DECISION_REVIEW

    DECISION_REVIEW --> HUMAN_APPROVAL

    HUMAN_APPROVAL --> ARTIFACT_GENERATION

    ARTIFACT_GENERATION --> COMPLETED

    REQUIREMENT_REVIEW --> HITL_REQUIRED
    VENDOR_ANALYSIS --> HITL_REQUIRED
    COMPARISON --> HITL_REQUIRED

    HITL_REQUIRED --> KNOWLEDGE_BUILDING
    HITL_REQUIRED --> REQUIREMENT_REVIEW
    HITL_REQUIRED --> VENDOR_ANALYSIS
    HITL_REQUIRED --> DECISION_REVIEW

    COMPLETED --> [*]
```

The orchestrator should know:

```text
What stage are we in?

What information is missing?

Which agent should execute?

Is HITL required?

Can the workflow move forward?

What output is expected from the current stage?
```

---

# 10 — Procurement Controller

The controller sits above individual agents.

```mermaid
flowchart TD

    ORCH["Purchase Orchestrator"]

    CTRL["Procurement Controller"]

    STATE["Purchase State"]

    QUALITY["Quality Checks"]
    POLICY["Policy Checks"]
    EVIDENCE["Evidence Checks"]
    READINESS["Readiness Checks"]
    HITL["HITL Decision"]

    ORCH --> CTRL

    CTRL --> STATE

    CTRL --> QUALITY
    CTRL --> POLICY
    CTRL --> EVIDENCE
    CTRL --> READINESS

    QUALITY --> HITL
    POLICY --> HITL
    EVIDENCE --> HITL
    READINESS --> HITL

    HITL --> NEXT["Next Workflow Stage"]
```

### Controller asks

```text
Are requirements complete?

Are mandatory requirements identified?

Are vendor responses sufficiently covered?

Are critical comparison cells backed by evidence?

Are evaluation criteria defined?

Are unresolved conflicts present?

Is human approval required?

Can the project move forward?
```

---

# 11 — Intake Agent

```mermaid
sequenceDiagram

    participant U as User
    participant I as Intake Agent
    participant K as Purchase Intelligence
    participant C as Controller

    U->>I: Describe purchase / upload initial files

    I->>K: Create initial purchase context

    I->>I: Identify missing information

    I->>C: Request readiness check

    C-->>I: Missing critical information

    I->>U: Ask targeted clarification

    U->>I: Provide answer

    I->>K: Update purchase context

    C->>C: Re-evaluate readiness

    C-->>I: Continue
```

### Important

The agent should **not** ask every possible procurement question.

It should ask only questions where:

```text
uncertainty × business impact
```

is high.

---

# 12 — Requirement Intelligence

```mermaid
flowchart TD

    INPUT["Business Information"]

    DOC["Requirement Documents"]
    CHAT["Conversation"]
    EMAIL["Emails"]
    SPEC["Technical Specifications"]

    INPUT --> DOC
    INPUT --> CHAT
    INPUT --> EMAIL
    INPUT --> SPEC

    DOC --> AGENT["Requirement Intelligence Agent"]
    CHAT --> AGENT
    EMAIL --> AGENT
    SPEC --> AGENT

    AGENT --> CLASSIFY["Classify Requirement"]

    CLASSIFY --> BUSINESS["Business"]
    CLASSIFY --> TECH["Technical"]
    CLASSIFY --> COMMERCIAL["Commercial"]
    CLASSIFY --> COMPLIANCE["Compliance"]
    CLASSIFY --> OPERATIONAL["Operational"]

    BUSINESS --> NORMALIZE["Normalize"]
    TECH --> NORMALIZE
    COMMERCIAL --> NORMALIZE
    COMPLIANCE --> NORMALIZE
    OPERATIONAL --> NORMALIZE

    NORMALIZE --> PRIORITY["Mandatory / Preferred / Informational"]

    PRIORITY --> EVIDENCE["Attach Source Evidence"]

    EVIDENCE --> KB["Purchase Intelligence"]
```

---

# 13 — Document Intelligence

```mermaid
flowchart TD

    FILE["Uploaded File"]

    CLASS["Document Classification"]

    PARSE["Document Parsing"]

    STRUCT["Structure Detection"]

    EXTRACT["Information Extraction"]

    NORMALIZE["Normalization"]

    VALIDATE["Validation"]

    EVIDENCE["Evidence Creation"]

    FILE --> CLASS
    CLASS --> PARSE
    PARSE --> STRUCT
    STRUCT --> EXTRACT
    EXTRACT --> NORMALIZE
    NORMALIZE --> VALIDATE
    VALIDATE --> EVIDENCE
```

### Supported document types

```text
PDF
DOCX
XLSX
CSV
PPTX
Email
Images / scanned documents
```

The output should **not simply be text chunks**.

It should produce structured procurement information.

---

# 14 — Vendor Intelligence Agent

```mermaid
flowchart TD

    DOCS["Vendor Documents"]

    DOCS --> PARSE["Document Intelligence"]

    PARSE --> VENDOR_AGENT["Vendor Intelligence Agent"]

    VENDOR_AGENT --> PROFILE["Vendor Profile"]

    PROFILE --> CAP["Capabilities"]
    PROFILE --> PRICE["Pricing"]
    PROFILE --> SLA["SLA"]
    PROFILE --> TECH["Technical Response"]
    PROFILE --> COMP["Compliance"]
    PROFILE --> IMPL["Implementation"]
    PROFILE --> ASSUMPTION["Assumptions"]
    PROFILE --> EXCEPTION["Exceptions"]

    CAP --> NORMALIZE["Vendor Normalization"]
    PRICE --> NORMALIZE
    SLA --> NORMALIZE
    TECH --> NORMALIZE
    COMP --> NORMALIZE
    IMPL --> NORMALIZE
    ASSUMPTION --> NORMALIZE
    EXCEPTION --> NORMALIZE

    NORMALIZE --> EVIDENCE["Evidence Layer"]

    EVIDENCE --> PROJECT["Purchase Intelligence"]
```

---

# 15 — Evidence Architecture

This should be treated as a first-class system capability.

```mermaid
flowchart LR

    SOURCE["Source Document"]

    CHUNK["Relevant Section"]

    CLAIM["Extracted Claim"]

    FACT["Normalized Fact"]

    EVAL["Evaluation"]

    DECISION["Decision"]

    SOURCE --> CHUNK
    CHUNK --> CLAIM
    CLAIM --> FACT
    FACT --> EVAL
    EVAL --> DECISION
```

Example:

```text
Vendor_B_SLA.pdf
        ↓
Page 14
        ↓
"Response within 8 business hours"
        ↓
sla_response_time = 8 hours
        ↓
Requirement = <= 4 hours
        ↓
FAIL
        ↓
Vendor B SLA Risk
```

This creates the traceability chain:

```text
Decision
   ↓
Evaluation
   ↓
Fact
   ↓
Claim
   ↓
Source
```

---

# 16 — Knowledge Builder

```mermaid
flowchart TD

    DOC["Documents"]
    CONV["Conversation"]
    REQ["Requirements"]
    VENDOR["Vendor Data"]
    EVIDENCE["Evidence"]

    DOC --> KB["Knowledge Builder"]
    CONV --> KB
    REQ --> KB
    VENDOR --> KB
    EVIDENCE --> KB

    KB --> ENTITY["Entity Resolution"]

    ENTITY --> REL["Relationship Detection"]

    REL --> GRAPH["Purchase Knowledge Graph"]

    GRAPH --> RETRIEVAL["Hybrid Retrieval"]

    RETRIEVAL --> AGENTS["Procurement Agents"]
```

---

# 17 — Hybrid Knowledge Architecture

Do not rely exclusively on Graph RAG.

Use three complementary representations.

```mermaid
flowchart TD

    KNOW["Purchase Knowledge"]

    GRAPH["Knowledge Graph"]
    VECTOR["Vector Store"]
    SQL["Structured Store"]
    EVIDENCE["Evidence Store"]

    KNOW --> GRAPH
    KNOW --> VECTOR
    KNOW --> SQL
    KNOW --> EVIDENCE

    GRAPH --> REL["Relationships"]
    VECTOR --> SEMANTIC["Semantic Retrieval"]
    SQL --> EXACT["Structured Queries"]
    EVIDENCE --> TRACE["Source Traceability"]

    REL --> AI["AI Reasoning"]
    SEMANTIC --> AI
    EXACT --> AI
    TRACE --> AI
```

### Each store has a different job

|Layer|Purpose|
|---|---|
|Graph|relationships|
|Vector|semantic retrieval|
|SQL|exact structured data|
|Evidence|traceability|

---

# 18 — Evaluation Agent

This is where requirements and vendors meet.

```mermaid
flowchart LR

    REQ["Requirements"]

    CRITERIA["Evaluation Criteria"]

    VENDOR["Vendor Facts"]

    EVIDENCE["Evidence"]

    RULES["Business Rules"]

    EVAL["Evaluation Agent"]

    RESULT["Evaluation Result"]

    REQ --> EVAL
    CRITERIA --> EVAL
    VENDOR --> EVAL
    EVIDENCE --> EVAL
    RULES --> EVAL

    EVAL --> RESULT
```

Possible result states:

```text
MEETS
PARTIAL
FAILS
NOT_SPECIFIED
NOT_APPLICABLE
CONFLICTING
```

---

# 19 — Deterministic Scoring

LLM reasoning should not directly determine numerical scores.

```mermaid
flowchart TD

    FACTS["Normalized Vendor Facts"]

    RULES["Evaluation Rules"]

    WEIGHTS["Criteria Weights"]

    ENGINE["Deterministic Scoring Engine"]

    SCORE["Vendor Score"]

    RANK["Ranking"]

    FACTS --> ENGINE
    RULES --> ENGINE
    WEIGHTS --> ENGINE

    ENGINE --> SCORE
    SCORE --> RANK
```

Example:

```text
Technical       40%
Commercial      30%
Risk            20%
Compliance      10%

              ↓

Deterministic Score

              ↓

Vendor Ranking
```

---

# 20 — Comparison Agent

The comparison agent should answer:

```text
What is different?

Why is it different?

Is the difference important?

What is the business impact?

What evidence supports the difference?
```

```mermaid
flowchart TD

    V1["Vendor A"]
    V2["Vendor B"]
    V3["Vendor C"]

    REQ["Common Requirements"]

    V1 --> COMP["Comparison Agent"]
    V2 --> COMP
    V3 --> COMP

    REQ --> COMP

    COMP --> SAME["Similarities"]
    COMP --> DIFF["Differences"]
    COMP --> GAP["Gaps"]
    COMP --> TRADE["Trade-offs"]
    COMP --> EXCEPT["Exceptions"]

    SAME --> DECISION["Decision Intelligence"]
    DIFF --> DECISION
    GAP --> DECISION
    TRADE --> DECISION
    EXCEPT --> DECISION
```

---

# 21 — Risk Agent

```mermaid
flowchart TD

    EVIDENCE["Vendor Evidence"]

    EVAL["Evaluation Results"]

    COMM["Commercial Data"]

    TECH["Technical Data"]

    CONTRACT["Contract / SLA Data"]

    RISK_AGENT["Risk Agent"]

    EVIDENCE --> RISK_AGENT
    EVAL --> RISK_AGENT
    COMM --> RISK_AGENT
    TECH --> RISK_AGENT
    CONTRACT --> RISK_AGENT

    RISK_AGENT --> R1["Technical Risk"]
    RISK_AGENT --> R2["Commercial Risk"]
    RISK_AGENT --> R3["Compliance Risk"]
    RISK_AGENT --> R4["Implementation Risk"]
    RISK_AGENT --> R5["Vendor Risk"]

    R1 --> REGISTER["Risk Register"]
    R2 --> REGISTER
    R3 --> REGISTER
    R4 --> REGISTER
    R5 --> REGISTER
```

---

# 22 — Decision Intelligence

This is the highest-level reasoning layer.

```mermaid
flowchart TD

    EVAL["Evaluation"]
    COMP["Comparison"]
    RISK["Risk"]
    SCORE["Scores"]
    BUSINESS["Business Objective"]
    CONSTRAINT["Business Constraints"]

    DECISION["Decision Intelligence Agent"]

    EVAL --> DECISION
    COMP --> DECISION
    RISK --> DECISION
    SCORE --> DECISION
    BUSINESS --> DECISION
    CONSTRAINT --> DECISION

    DECISION --> BESTFIT["Best Overall Fit"]
    DECISION --> LOWESTCOST["Lowest Cost"]
    DECISION --> LOWRISK["Lowest Risk"]
    DECISION --> TRADEOFF["Trade-offs"]
    DECISION --> UNKNOWN["Critical Unknowns"]
    DECISION --> SCENARIO["Decision Scenarios"]

    BESTFIT --> RECOMMEND["Recommendation"]
    LOWESTCOST --> RECOMMEND
    LOWRISK --> RECOMMEND
    TRADEOFF --> RECOMMEND
    UNKNOWN --> RECOMMEND
    SCENARIO --> RECOMMEND
```

The system should say:

> **Vendor A is the strongest overall fit.**

rather than pretending:

> **AI selected Vendor A.**

---

# 23 — Human-in-the-Loop

HITL should exist at specific decision gates.

```mermaid
flowchart TD

    AI["AI Analysis"]

    CHECK["Controller"]

    AUTO["Continue Automatically"]

    HITL["Human Review"]

    APPROVE["Approve"]

    MODIFY["Modify"]

    REJECT["Reject"]

    AI --> CHECK

    CHECK --> AUTO
    CHECK --> HITL

    HITL --> APPROVE
    HITL --> MODIFY
    HITL --> REJECT

    MODIFY --> AI
    APPROVE --> NEXT["Next Stage"]
    REJECT --> REWORK["Rework"]
```

### HITL triggers

```text
Critical requirement ambiguity
        OR
Conflicting vendor information
        OR
Missing critical evidence
        OR
Policy violation
        OR
Low confidence
        OR
Final recommendation
        OR
Final artifact approval
```

---

# 24 — Final Decision Model

Everything eventually converges here.

```mermaid
flowchart TD

    PROJECT["Purchase"]

    REQ["Requirements"]
    CRITERIA["Criteria"]
    VENDOR["Vendor Intelligence"]
    EVIDENCE["Evidence"]
    SCORE["Scores"]
    RISK["Risks"]
    COMP["Comparison"]

    DECISION["Purchase Decision Model"]

    PROJECT --> DECISION
    REQ --> DECISION
    CRITERIA --> DECISION
    VENDOR --> DECISION
    EVIDENCE --> DECISION
    SCORE --> DECISION
    RISK --> DECISION
    COMP --> DECISION

    DECISION --> RECOMMEND["Recommendation"]

    RECOMMEND --> HUMAN["Human Decision"]

    HUMAN --> FINAL["Approved Decision"]
```

---

# 25 — Artifact Generation

Artifacts should be **rendered from the Decision Model**, not independently generated by separate agents.

```mermaid
flowchart TD

    DECISION["Approved Decision Model"]

    ARTIFACT["Artifact Agent"]

    EXCEL["Comparison Matrix"]
    PPT["Executive Presentation"]

    DECISION --> ARTIFACT

    ARTIFACT --> EXCEL
    ARTIFACT --> PPT
```

### Excel

```text
Executive Summary
Requirements Matrix
Vendor Comparison
Technical Evaluation
Commercial Evaluation
Risk Assessment
Scoring
Evidence References
```

### PPT

```text
Purchase Overview
Business Requirements
Vendor Landscape
Comparison
Commercial Analysis
Risk
Trade-offs
Recommendation
Decision Required
```

---

# 26 — Complete End-to-End Agent Graph

```mermaid
flowchart TD

    USER["Business User"]

    APP["Procurement Workspace"]

    ORCH["Purchase Orchestrator"]

    CTRL["Procurement Controller"]

    INTAKE["Intake Agent"]

    REQ["Requirement Agent"]

    CLARIFY["Clarification Agent"]

    DOC["Document Intelligence"]

    VENDOR["Vendor Intelligence"]

    EVIDENCE["Evidence Agent"]

    KB["Knowledge Builder"]

    EVAL["Evaluation Agent"]

    COMP["Comparison Agent"]

    RISK["Risk Agent"]

    SCORE["Scoring Engine"]

    DECISION["Decision Intelligence"]

    RECOMMEND["Recommendation"]

    HITL["Human Approval"]

    ART["Artifact Agent"]

    EXCEL["Excel"]

    PPT["PPT"]

    USER --> APP
    APP --> ORCH
    ORCH --> CTRL

    CTRL --> INTAKE

    INTAKE --> REQ
    REQ --> CLARIFY

    CLARIFY --> DOC
    DOC --> VENDOR
    VENDOR --> EVIDENCE

    EVIDENCE --> KB

    KB --> EVAL

    EVAL --> COMP
    COMP --> RISK
    RISK --> SCORE

    SCORE --> DECISION
    COMP --> DECISION
    RISK --> DECISION

    DECISION --> RECOMMEND

    RECOMMEND --> HITL

    HITL --> ART

    ART --> EXCEL
    ART --> PPT

    EXCEL --> APP
    PPT --> APP
```

---

# 27 — Runtime Architecture

The logical agent graph sits on top of runtime infrastructure.

```mermaid
flowchart TD

    UI["Web Application"]

    API["Application API"]

    ORCH["Agent Orchestrator"]

    AGENT["Agent Runtime"]

    TOOLS["Tool Layer"]

    KNOW["Knowledge Layer"]

    DATA["Enterprise Data"]

    UI --> API
    API --> ORCH

    ORCH --> AGENT

    AGENT --> TOOLS
    AGENT --> KNOW

    TOOLS --> DATA
```

### Tool layer

```text
Document Parser
Search
Retrieval
Database
Graph Query
Calculator
Scoring
Excel
PPT
Validation
```

---

# 28 — Agent Tool Access

Agents should have **bounded tools**.

```mermaid
flowchart LR

    INTAKE["Intake Agent"]
    REQ["Requirement Agent"]
    VENDOR["Vendor Agent"]
    EVAL["Evaluation Agent"]
    DECISION["Decision Agent"]

    INTAKE --> T1["Project Context Tool"]

    REQ --> T2["Document Search"]
    REQ --> T3["Requirement Store"]

    VENDOR --> T4["Vendor Document Search"]
    VENDOR --> T5["Vendor Store"]

    EVAL --> T6["Evidence Retrieval"]
    EVAL --> T7["Scoring Engine"]

    DECISION --> T8["Comparison Store"]
    DECISION --> T9["Risk Store"]
```

This is important for:

- security
    
- debugging
    
- observability
    
- cost control
    
- predictable behavior
    
- least-privilege access
    

---

# 29 — Observability

Every agent action should produce an execution record.

```mermaid
flowchart TD

    AGENT["Agent Execution"]

    TRACE["Trace"]

    INPUT["Input Context"]
    TOOL["Tool Calls"]
    OUTPUT["Output"]
    EVIDENCE["Evidence Used"]
    CONF["Confidence"]
    COST["Token / Cost"]
    TIME["Latency"]

    AGENT --> TRACE

    TRACE --> INPUT
    TRACE --> TOOL
    TRACE --> OUTPUT
    TRACE --> EVIDENCE
    TRACE --> CONF
    TRACE --> COST
    TRACE --> TIME
```

This becomes extremely important when someone asks:

> “Why did the AI say Vendor B failed?”

You should be able to reconstruct the execution.

---

# 30 — Final Architecture Mental Model

The entire system can be reduced to:

```text
                         USER
                           │
                           ▼
                ┌─────────────────────┐
                │ PROCUREMENT WORKSPACE│
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ PURCHASE ORCHESTRATOR│
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ PROCUREMENT CONTROLLER│
                └──────────┬──────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
   UNDERSTAND           KNOWLEDGE           ANALYZE
       │                   │                   │
   Intake              Documents          Evaluation
   Requirements        Vendors             Comparison
   Clarification       Evidence            Risk
                       Graph               Scoring
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                 DECISION INTELLIGENCE
                           │
                           ▼
                    HUMAN APPROVAL
                           │
                           ▼
                     DECISION MODEL
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
              EXCEL                 PPT
```

---

# 31 — The Core Architecture Rule

> [!important]  
> **Agents are not the architecture.**
> 
> The **Purchase Intelligence + Procurement State Machine + Controller** are the architecture.
> 
> Agents are reasoning components operating inside that architecture.

This distinction will make the eventual implementation much cleaner.

---

# 32 — Recommended Agent Hierarchy

```text
PROCUREMENT AI SYSTEM
│
├── ORCHESTRATION
│   ├── Purchase Orchestrator
│   └── Procurement Controller
│
├── UNDERSTANDING
│   ├── Intake Agent
│   ├── Requirement Agent
│   └── Clarification Agent
│
├── KNOWLEDGE
│   ├── Document Intelligence
│   ├── Vendor Intelligence
│   ├── Evidence Agent
│   └── Knowledge Builder
│
├── DECISION INTELLIGENCE
│   ├── Evaluation Agent
│   ├── Comparison Agent
│   ├── Risk Agent
│   ├── Scoring Engine
│   └── Decision Intelligence Agent
│
└── DELIVERY
    ├── Artifact Agent
    ├── Excel Generator
    └── PPT Generator
```

The **next architecture document I would create after this is not another agent diagram**. It should be the **`Purchase Intelligence Data Model`** — showing the exact entities, states, relationships, evidence objects, agent inputs/outputs, and how the Graph + SQL + Vector layers represent one purchase. That will give developers the concrete contract they need to implement this agent graph.