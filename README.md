# Procure AI Workspace

> **AI-powered procurement workspace for transforming fragmented purchase information into a traceable, evidence-backed vendor decision.**

---

## 🎯 Final Goal: End-to-End Flow

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

### Core Architecture Concept

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

> **The product in one sentence:**  
> Multiple procurement inputs → one Purchase Knowledge Graph → AI-assisted comparison and decision intelligence → business-ready procurement outputs.

---

## 🚀 Sprint 1 Deliverables

### Goal
```text
Login Databricks SSO ➔ Profile Page ➔ Dashboard ➔ Chat Interface
```

### Deliverables Checklist

- [ ] **1. Deploy Databricks App** — Hosting & deployment configuration for the workspace app on Databricks
- [ ] **2. Flask App** — Core web application framework and API endpoints
- [ ] **3. User Table** — User model, persistence, and profile data structures
- [ ] **4. X-Forwarded Header Handling** — Secure proxy, Databricks SSO header & authentication forwarding
- [ ] **5. Telemetry** — Logging, metrics tracking, and observability
- [ ] **6. Chat Agent** — Conversational agent core & message routing
- [ ] **7. Model Registry** — Model registry integration and LLM endpoint configuration
- [ ] **8. Context Management** — Memory buffer, token budget, and conversation history
- [ ] **9. User Tools & MCP** — External integrations:
  - SharePoint
  - Outlook
  - OneDrive
  - User Memory
- [ ] **10. HITL (Human-in-the-Loop)** — User approval gates, clarifications, and feedback handling
- [ ] **11. Session Management** — Multi-turn session persistence and state recovery
- [ ] **12. Templates** — Standardized prompt templates and artifact output schemas
