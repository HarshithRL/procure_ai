# Procure AI Workspace

> **AI-powered procurement workspace for transforming fragmented purchase information into a traceable, evidence-backed vendor decision.**

---

## 01 — Use Case

### Vendor Comparison for Business Procurement

A business unit initiates a purchase and receives information from multiple vendors through different channels.

The information is fragmented across documents, emails, conversations, spreadsheets, presentations, and other business artifacts.

The objective of **Procure AI Workspace** is to bring this information into a single project workspace, build a structured understanding of the purchase, assist the user throughout the procurement journey, and produce decision-ready comparison and presentation artifacts.

```text
Fragmented Procurement Information
              ↓
       Procure AI Workspace
              ↓
    Structured Project Intelligence
              ↓
       Vendor Comparison
              ↓
      Business Decision Support
```

---

# 02 — Procurement Paths

The organization can have two primary purchasing paths:

### Direct Purchase

A business-driven purchase where the business requirement, technical specifications, existing supplier context, or operational need drives the procurement process.

### Indirect Purchase

A procurement/category-driven purchase where sourcing, supplier evaluation, commercial comparison, and procurement processes play a larger role.

The two workflows may differ, but the **expected intelligence and output are largely common**.

```text
                 PROCUREMENT
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
    Direct Purchase        Indirect Purchase
          │                       │
          └───────────┬───────────┘
                      ↓
             Common AI Intelligence
                      ↓
             Vendor Comparison
                      ↓
              Decision Artifacts
```

---

# 03 — Expected Inputs

The workspace must be capable of accepting information from multiple sources.

## File Inputs

The user may upload procurement-related files such as:

- PDF
    
- Excel / XLSX
    
- CSV
    
- PowerPoint / PPTX
    
- Word / DOCX
    
- Text / TXT
    
- Other relevant business documents
    

Typical examples:

```text
Business Requirement
Technical Specification
Vendor Proposal
Vendor Quotation
Pricing Sheet
Contract
SLA
Compliance Document
RFP / RFQ
Scope of Work
Existing Comparison Sheet
Previous Purchase Documents
```

---

## Conversation Inputs

### User ↔ AI Conversation

The user can provide context directly through the AI assistant.

Example:

> We need to procure laptops for 1,200 employees across Europe. Security certification is mandatory and we prefer a three-year support agreement.

This conversation becomes part of the **project knowledge**.

---

## Email Inputs

The workspace should also support procurement information originating from email conversations.

Examples:

```text
Business ↔ Procurement
Procurement ↔ Vendor
Vendor ↔ Business
Procurement ↔ Stakeholder
```

Emails may contain:

- Requirements
    
- Clarifications
    
- Vendor responses
    
- Commercial information
    
- Negotiation details
    
- Decisions
    
- Approvals
    
- Exceptions
    
- Additional context
    

Email information should become traceable project evidence rather than being treated as isolated text.

---

# 04 — Unified Project Knowledge

All inputs converge into one project-level knowledge layer.

```text
                 PURCHASE PROJECT
                        │
       ┌────────────────┼────────────────┐
       ↓                ↓                ↓
     Files        AI Conversation       Emails
       │                │                │
       └────────────────┼────────────────┘
                        ↓
               Project Knowledge
                        │
       ┌────────────────┼────────────────┐
       ↓                ↓                ↓
 Requirements       Vendors           Evidence
       │                │                │
       └────────────────┼────────────────┘
                        ↓
                Decision Intelligence
```

The same information should remain available throughout the project lifecycle.

---

# 05 — Core Product Capability

## AI Assistant Throughout the Journey

The AI Assistant is continuously available inside the purchase project.

It should help users:

- Understand uploaded information
    
- Extract requirements
    
- Identify vendors
    
- Find missing information
    
- Ask clarification questions
    
- Compare vendors
    
- Explain differences
    
- Identify risks and gaps
    
- Trace information back to evidence
    
- Answer procurement questions
    
- Prepare the comparison matrix
    
- Prepare the business presentation
    

The assistant should not be limited to a single chat screen.

It is a **persistent project intelligence layer**.

```text
Create Purchase
      ↓
AI Intake
      ↓
Upload / Connect Information
      ↓
AI Understanding
      ↓
HITL Clarification
      ↓
Knowledge Building
      ↓
Vendor Analysis
      ↓
Comparison
      ↓
Decision Support
      ↓
Artifact Generation
```

---

# 06 — Core Expected Outputs

The product has three primary outputs.

## 1. Complete Comparison Matrix

The primary analytical output of the system.

The comparison matrix should be generated from the structured project knowledge and vendor evidence.

Possible formats:

- Excel / XLSX
    
- CSV
    
- Word / DOCX
    
- Other business-consumable formats
    

The matrix can contain:

```text
Vendor Information
Requirement Comparison
Technical Comparison
Commercial Comparison
Pricing
Compliance
SLA
Risk
Scoring
Ranking
Assumptions
Exceptions
Evidence References
```

Example:

```text
Requirement        Vendor A    Vendor B    Vendor C
----------------------------------------------------
Technical Fit      Meets       Partial     Meets
SLA                Meets       Fails       Meets
Security           Meets       Meets       Partial
Price              €420K       €390K        €450K
Risk               Low         Medium       High
----------------------------------------------------
Overall Score       91          78           84
```

Each important value should ideally be traceable to its source evidence.

---

## 2. PPT Presentation Preparation

The system should automatically transform the approved comparison into a business-ready presentation.

Typical output:

```text
Slide 1   Purchase Overview
Slide 2   Business Requirement
Slide 3   Vendor Landscape
Slide 4   Evaluation Criteria
Slide 5   Technical Comparison
Slide 6   Commercial Comparison
Slide 7   Risk / Gap Analysis
Slide 8   Vendor Ranking
Slide 9   AI Decision Support
Slide 10  Decision Required
```

The PPT should be generated from the same project knowledge and comparison model used to create the matrix.

```text
                    PROJECT KNOWLEDGE
                           │
                           ↓
                  COMPARISON ENGINE
                     /          \
                    ↓            ↓
          Comparison Matrix      PPT
              XLSX/CSV/etc.    Presentation
```

This ensures that the Excel matrix and PPT do not contain conflicting information.

---

## 3. AI Assistant Throughout the Journey

The AI assistant remains available from project creation through final decision support.

Examples:

> Which vendor has the strongest technical fit?

> What requirements does Vendor B fail?

> Show me all pricing differences.

> Why is Vendor A ranked first?

> Which assumptions are still unresolved?

> Find the evidence for this comparison cell.

> Prepare the executive summary for the business meeting.

```text
              AI ASSISTANT
                   │
     ┌─────────────┼─────────────┐
     ↓             ↓             ↓
   Intake      Analysis      Decision
     ↓             ↓             ↓
  Clarify      Compare       Explain
     ↓             ↓             ↓
  Understand     Risks       Prepare
                               ↓
                         Generate Outputs
```

---

# 07 — End-to-End Product Flow

```text
                    ┌─────────────────────┐
                    │     DASHBOARD       │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │   CREATE PURCHASE   │
                    └──────────┬──────────┘
                               ↓
                    Direct / Indirect
                               ↓
                  ┌──────────────────────┐
                  │     AI INTAKE        │
                  └──────────┬───────────┘
                             ↓
          ┌──────────────────┼──────────────────┐
          ↓                  ↓                  ↓
      Documents          AI Chat            Emails
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
                  ┌──────────────────────┐
                  │ PROJECT KNOWLEDGE    │
                  └──────────┬───────────┘
                             ↓
                ┌────────────────────────┐
                │ AI + HITL CLARIFICATION│
                └────────────┬───────────┘
                             ↓
                ┌────────────────────────┐
                │ REQUIREMENT INTELLIGENCE│
                └────────────┬───────────┘
                             ↓
                ┌────────────────────────┐
                │ VENDOR INTELLIGENCE    │
                └────────────┬───────────┘
                             ↓
                ┌────────────────────────┐
                │ COMPARISON & ANALYSIS  │
                └────────────┬───────────┘
                             ↓
                ┌────────────────────────┐
                │ HUMAN REVIEW / APPROVAL│
                └────────────┬───────────┘
                             ↓
                 ┌───────────┴───────────┐
                 ↓                       ↓
        COMPARISON MATRIX              PPT
         XLSX / CSV / DOCX         Presentation
                 \                       /
                  \                     /
                   └───────┬───────────┘
                           ↓
                 PROCUREMENT DECISION
```

---

# 08 — Core Product Principle

> **Multiple inputs → one project intelligence layer → continuous AI assistance → multiple decision-ready outputs.**

The application should therefore be viewed as a:

## **Procurement Decision Workspace**

rather than simply:

- Vendor comparison software
    
- Document analysis software
    
- AI chatbot
    
- Excel generator
    
- PPT generator
    

All of these are capabilities inside the workspace.

---

# 09 — North Star



>  **One Purchase → One Intelligent Workspace → One Defensible Decision**
The workspace should allow a user to start with fragmented information and finish with a decision that can be understood, challenged, and presented.
Turn fragmented procurement information into a complete, explainable, and business-ready vendor decision.**

### Inputs

**Files + Emails + Conversations + User Knowledge**

### Intelligence

**Requirements + Vendors + Evidence + Comparison + Risk + Decision Support**

### Outputs

**Comparison Matrix + PPT + AI Assistant**



---

## Open Questions

- What exactly differs between Direct and Indirect procurement?
    
- What information is mandatory before comparison can begin?
    
- What evaluation criteria are organization-specific?
    
- Which parts of the comparison should be deterministic?
    
- Which parts require LLM reasoning?
    
- What evidence must be retained for auditability?
    
- How should users override or modify AI-generated analysis?
    
- How should historical vendor/project knowledge be reused?
    
- What should belong in the MVP versus the future platform?
    

---

## Current Focus

> **Vendor Comparison as the first concrete AI procurement use case.**

The immediate objective is to design the smallest useful version of the workspace that can reliably transform vendor and purchase information into an evidence-backed comparison matrix and business-ready decision artifact.