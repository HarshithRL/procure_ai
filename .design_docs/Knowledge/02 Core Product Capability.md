The Procure AI Workspace combines multiple AI capabilities around a single **Purchase Project**.

The core capabilities are:

```text
                    PURCHASE PROJECT
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
       AI Assistant    Knowledge      Document
                       Graph          Intelligence
            │              │              │
            └──────────────┼──────────────┘
                           ↓
                 Requirement Intelligence
                           ↓
                   Vendor Intelligence
                           ↓
                 Comparison & Analysis
                           ↓
                  Decision Intelligence
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       Comparison Matrix              PPT
```

---

## 05.1 — AI Assistant

The AI Assistant remains available throughout the entire purchase lifecycle.

It helps the user:

- Understand the purchase
    
- Provide additional context
    
- Review uploaded documents
    
- Ask questions
    
- Clarify ambiguities
    
- Identify missing information
    
- Analyze vendors
    
- Compare requirements
    
- Investigate risks and gaps
    
- Explain AI findings
    
- Prepare comparison artifacts
    
- Prepare business presentations
    

The assistant should maintain **project-level context** rather than behaving like an isolated chatbot.

---

## 05.2 — Knowledge Graph Building

The workspace continuously builds a **Purchase Knowledge Graph** from the information provided by the user and discovered from project sources.

### Knowledge Sources

```text
Files
   │
   ├── PDF
   ├── Excel
   ├── Word
   ├── PowerPoint
   └── Other Documents

Emails
   │
   └── Email Conversations

AI Conversations
   │
   └── User-provided Context

Business / Procurement Data
```

These sources are processed into structured project knowledge.

### Knowledge Graph

```text
                    PURCHASE PROJECT
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
   Requirements        Vendors           Stakeholders
        │                  │                  │
        ↓                  ↓                  ↓
   Criteria           Proposals          Decisions
        │                  │
        ↓                  ↓
   Constraints         Pricing
                           │
                           ↓
                         SLA
                           │
                           ↓
                       Compliance
```

---

## 05.3 — Knowledge Entities

The graph can contain entities such as:

```text
Purchase
Requirement
Sub-Requirement
Evaluation Criteria
Vendor
Vendor Contact
Proposal
Quotation
Product / Service
Pricing
Contract
SLA
Compliance Requirement
Risk
Assumption
Stakeholder
Decision
Conversation
Email
Document
Evidence
Score
Recommendation
```

---

## 05.4 — Knowledge Relationships

The intelligence layer should not only store entities; it should understand their relationships.

Examples:

```text
Purchase
 ├── HAS_REQUIREMENT → Requirement
 ├── HAS_VENDOR → Vendor
 ├── HAS_DOCUMENT → Document
 ├── HAS_STAKEHOLDER → Stakeholder
 └── HAS_DECISION → Decision
```

```text
Vendor
 ├── SUBMITTED → Proposal
 ├── QUOTED → Price
 ├── RESPONDED_TO → Requirement
 ├── OFFERS → Product / Service
 └── HAS_SLA → SLA
```

```text
Requirement
 ├── DEFINED_IN → Document
 ├── DISCUSSED_IN → Conversation
 ├── EVALUATED_BY → Criteria
 └── SATISFIED_BY → Vendor Response
```

```text
Comparison Result
 ├── COMPARES → Requirement + Vendor
 ├── SUPPORTED_BY → Evidence
 ├── PRODUCES → Score
 └── CONTRIBUTES_TO → Recommendation
```

---

## 05.5 — Evidence Graph

A critical capability is maintaining a connection between an AI conclusion and its original evidence.

```text
Vendor B
    │
    ↓
Requirement: 4-hour Critical SLA
    │
    ↓
Comparison Result: FAIL
    │
    ↓
Evidence
    │
    ↓
Vendor_B_SLA.pdf
    │
    ↓
Page 12
    │
    ↓
"Critical incidents addressed within
8 business hours."
```

This enables the user to ask:

> **Why did Vendor B fail this requirement?**

The system can answer with the result **and the supporting evidence**.

---

## 05.6 — Knowledge Acquisition + HITL

Knowledge graph construction should be an iterative process.

The system continuously evaluates:

- What is known?
    
- What is missing?
    
- What is ambiguous?
    
- What conflicts?
    
- What requires human confirmation?
    

```text
             New Information
                    ↓
             AI Extraction
                    ↓
             Knowledge Graph
                    ↓
          Confidence / Validation
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
   Sufficient                Uncertain
        ↓                       ↓
    Continue              Ask User / HITL
                                ↓
                         User Confirmation
                                ↓
                         Update Knowledge
```

This allows the AI to ask targeted questions such as:

> “The business requirement states a 4-hour SLA, while the latest vendor email states 8 hours. Which requirement should govern the evaluation?”

---

## 05.7 — Project Knowledge State

The system should maintain a measurable view of project readiness.

```text
Knowledge Readiness

Requirements        94%
Vendors              100%
Vendor Evidence       88%
Evaluation Criteria   100%
Stakeholders           90%
Critical Ambiguities     1
```

The system can then determine whether the project is:

```text
INITIAL
   ↓
UNDERSTANDING
   ↓
KNOWLEDGE_BUILDING
   ↓
READY_FOR_ANALYSIS
   ↓
ANALYSIS_COMPLETE
   ↓
READY_FOR_DECISION
```

---

## 05.8 — Requirement Intelligence

AI converts unstructured requirements into structured evaluation objects.

```text
Raw Requirement
      ↓
Requirement Extraction
      ↓
Normalization
      ↓
Classification
      ↓
Priority / Mandatory Status
      ↓
Evaluation Criteria
```

Possible classifications:

```text
Business
Technical
Commercial
Compliance
Security
Operational
Service / SLA
Implementation
Sustainability
```

---

## 05.9 — Vendor Intelligence

Vendor information is transformed into normalized vendor profiles.

```text
Vendor Documents
      ↓
Document Extraction
      ↓
Vendor Profile
      ↓
Product / Service Information
      ↓
Pricing
      ↓
SLA
      ↓
Compliance
      ↓
Requirement Responses
      ↓
Evidence
```

This creates a consistent representation even when different vendors submit information in completely different formats.

---

## 05.10 — Comparison Intelligence

The comparison engine evaluates:

```text
Requirement
      +
Evaluation Criteria
      +
Vendor Response
      +
Evidence
      +
Business Rules
      ↓
Comparison Result
```

Possible result states:

```text
MEETS
FAILS
PARTIAL
NOT_SPECIFIED
NOT_APPLICABLE
CONFLICTING
```

The system should distinguish **“No”** from **“Not stated”**.

---

## 05.11 — Decision Intelligence

Once sufficient project knowledge exists, the system can identify:

- Best technical fit
    
- Commercial differences
    
- Requirement gaps
    
- Vendor risks
    
- Trade-offs
    
- Exceptions
    
- Missing information
    
- Scenario differences
    
- Overall vendor ranking
    

The AI should provide **decision support**, not automatically make the final procurement decision.

---

## 05.12 — Artifact Generation

The structured knowledge and comparison model become the source for the final business artifacts.

```text
                 PROJECT KNOWLEDGE
                        │
                        ↓
                DECISION MODEL
                        │
             ┌──────────┴──────────┐
             ↓                     ↓
     Comparison Matrix             PPT
       XLSX / CSV / DOCX      Executive Summary
```

This ensures that the comparison matrix and PPT are generated from the **same underlying project truth**.

---

## 05.13 — Core Capability Stack

The overall intelligence stack can therefore be viewed as:

```text
┌───────────────────────────────────────────┐
│              USER EXPERIENCE               │
│ Dashboard • Workspace • AI Assistant       │
├───────────────────────────────────────────┤
│          DECISION INTELLIGENCE              │
│ Comparison • Risk • Scoring • Recommendation│
├───────────────────────────────────────────┤
│          VENDOR / REQUIREMENT INTELLIGENCE │
│ Vendor Profiles • Requirements • Criteria   │
├───────────────────────────────────────────┤
│             KNOWLEDGE GRAPH                │
│ Entities • Relationships • Evidence         │
├───────────────────────────────────────────┤
│           DOCUMENT INTELLIGENCE             │
│ PDF • Excel • PPT • Word • Email            │
├───────────────────────────────────────────┤
│               INPUT LAYER                  │
│ Files • Emails • Conversations • User Data │
└───────────────────────────────────────────┘
```

### Core Principle

> **Every input should contribute to a continuously evolving Purchase Knowledge Graph, and every AI output should be grounded in that project knowledge and its supporting evidence.**