

```mermaid
flowchart TD

    A[Business Purchase Need]
    B{Purchase Type}

    A --> B
    B --> C[Direct Procurement]
    B --> D[Indirect Procurement]

    C --> E[Create Purchase Project]
    D --> E

    E --> F[AI Intake]

    F --> G[Collect Project Information]

    G --> G1[Files]
    G --> G2[Emails]
    G --> G3[AI Conversation]
    G --> G4[Business Context]

    G1 --> H[Information Processing]
    G2 --> H
    G3 --> H
    G4 --> H

    H --> H1[Document Intelligence]
    H --> H2[Requirement Extraction]
    H --> H3[Vendor Extraction]

    H1 --> I[Project Knowledge]
    H2 --> I
    H3 --> I

    I --> I1[Requirements]
    I --> I2[Vendor Information]
    I --> I3[Evidence]
    I --> I4[Stakeholders]
    I --> I5[Business Rules]

    I --> J[Purchase Knowledge Graph]

    J --> K[Knowledge Validation]

    K --> L{Enough Knowledge?}

    L -->|No| M[HITL Clarification]
    M --> N[User Answers]
    N --> J

    L -->|Yes| O[Analysis Ready]

    O --> P[Vendor Comparison]

    P --> P1[Requirement Mapping]
    P --> P2[Vendor Response]
    P --> P3[Criteria Evaluation]
    P --> P4[Evidence Validation]
    P --> P5[Scoring]

    P --> Q[Decision Intelligence]

    Q --> Q1[Strengths]
    Q --> Q2[Weaknesses]
    Q --> Q3[Risks]
    Q --> Q4[Gaps]
    Q --> Q5[Trade Offs]
    Q --> Q6[Recommendation]

    Q --> R[Human Review]

    R --> S{Approved?}

    S -->|No| T[Modify Information]
    T --> P

    S -->|Yes| U[Generate Outputs]

    U --> U1[Comparison Matrix]
    U --> U2[PPT Presentation]
    U --> U3[AI Assistant]

    U1 --> V[Business Decision]
    U2 --> V
    U3 --> V

    V --> W[Purchase Execution]
```

---

# Flow Explanation

## 1. Business Entry

```text
Business Purchase Need
        ↓
Direct / Indirect
        ↓
Purchase Project
```

Direct and indirect procurement have different business processes, but both eventually enter the same AI workspace.

---

## 2. Information Collection

The project can receive information from multiple sources:

```text
             Purchase Project
                    |
       +------------+------------+
       |            |            |
      Files       Emails      AI Chat
       |            |            |
       +------------+------------+
                    |
             Business Context
```

### Main inputs

- PDF
    
- Excel
    
- CSV
    
- PowerPoint
    
- Word
    
- Emails
    
- User conversation
    
- Business-provided information
    

---

# 3. Information Processing

The system converts unstructured information into structured project information.

```text
Files / Emails / Conversation
            |
            v
    Information Processing
            |
     +------+------+------+
     |      |      |      |
 Documents Requirements Vendors Evidence
```

This is where document intelligence, extraction, classification, normalization, and source tracking happen.

---

# 4. Project Knowledge

All information becomes part of the **Purchase Project Knowledge**.

```text
Purchase Knowledge
|
+-- Requirements
|
+-- Vendors
|
+-- Evidence
|
+-- Stakeholders
|
+-- Business Rules
|
+-- Decisions
|
+-- Conversations
```

The **Knowledge Graph** connects these entities.

Example:

```text
Requirement
    |
    +-- defined in --> Document
    |
    +-- discussed in --> Conversation
    |
    +-- answered by --> Vendor
    |
    +-- evaluated by --> Criteria
    |
    +-- supported by --> Evidence
```

---

# 5. Knowledge Validation

The AI checks whether enough information exists to perform a reliable comparison.

```text
Knowledge
   |
   v
Validation
   |
   +-- Missing information
   +-- Ambiguity
   +-- Conflicting information
   +-- Missing vendor response
   +-- Missing requirement
```

When something important is missing:

```text
AI detects uncertainty
        |
        v
AI asks user
        |
        v
User clarifies
        |
        v
Knowledge Graph updated
        |
        v
Validation again
```

This is the main **HITL loop**.

---

# 6. Comparison Intelligence

Once the project is ready:

```text
Requirements
      +
Evaluation Criteria
      +
Vendor Responses
      +
Evidence
      |
      v
Vendor Comparison
```

The comparison engine evaluates each vendor against the purchase requirements.

Example result states:

```text
MEETS
PARTIAL
FAILS
NOT SPECIFIED
NOT APPLICABLE
CONFLICTING
```

---

# 7. Decision Intelligence

The system then produces decision-support information.

```text
Vendor Comparison
       |
       +-- Strengths
       +-- Weaknesses
       +-- Gaps
       +-- Risks
       +-- Trade Offs
       +-- Scores
       +-- Ranking
       +-- Recommendation
```

The recommendation remains **decision support**, not an autonomous procurement decision.

---

# 8. Human Review

The business or procurement user reviews:

- Comparison
    
- Evidence
    
- Scores
    
- Risks
    
- Recommendation
    

The user can modify information or challenge AI findings.

```text
AI Analysis
    |
    v
Human Review
    |
    +---- Reject / Modify ----> Re-analysis
    |
    +---- Approve -----------> Output Generation
```

---

# 9. Core Outputs

The system has three primary outputs.

```text
                 Approved Analysis
                        |
            +-----------+-----------+
            |           |           |
            v           v           v
       Comparison      PPT      AI Assistant
         Matrix      Presentation
```

### Comparison Matrix

Possible formats:

```text
XLSX
CSV
DOCX
```

Contains:

- Vendor comparison
    
- Requirement mapping
    
- Commercial comparison
    
- Technical comparison
    
- Scoring
    
- Ranking
    
- Risks
    
- Evidence references
    

### PPT Presentation

Business-ready presentation containing:

- Purchase overview
    
- Requirements
    
- Vendor comparison
    
- Commercial analysis
    
- Risk analysis
    
- Recommendation
    
- Decision required
    

### AI Assistant

Available throughout the complete journey:

```text
Create
  ↓
Understand
  ↓
Analyze
  ↓
Compare
  ↓
Review
  ↓
Generate
```

The assistant is therefore **not a single step** in the workflow.

It is a **continuous interface over the Purchase Project intelligence**.

---

# Core Architecture Concept

```mermaid
flowchart LR

    A[Files]
    B[Emails]
    C[AI Conversation]
    D[Business Context]

    A --> E[Project Knowledge]
    B --> E
    C --> E
    D --> E

    E --> F[Knowledge Graph]

    F --> G[Requirement Intelligence]
    F --> H[Vendor Intelligence]
    F --> I[Evidence]

    G --> J[Comparison Engine]
    H --> J
    I --> J

    J --> K[Decision Intelligence]

    K --> L[Comparison Matrix]
    K --> M[PPT]
    K --> N[AI Assistant]
```

## The product in one sentence

> **Multiple procurement inputs → one Purchase Knowledge Graph → AI-assisted comparison and decision intelligence → business-ready procurement outputs.**