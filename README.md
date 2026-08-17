# Procure AI Workspace

> **AI-powered procurement workspace for transforming fragmented purchase information into traceable, evidence-backed vendor decisions.**

---

## Overview

**Procure AI Workspace** is an AI-native workspace designed to support business and procurement teams throughout the entire purchase lifecycle (Direct and Indirect procurement).

Instead of relying on disconnected spreadsheets and manual document cross-referencing, Procure AI Workspace standardizes and accelerates the path from raw proposals to executive-ready decision deliverables:

```text
Purchase Requirements & Vendor Documents
                  │
                  ▼
   Document & Evidence Extraction
                  │
                  ▼
     Normalization & Schema Mapping
                  │
                  ▼
 Requirement ↔ Vendor Evaluation Matrix
                  │
                  ▼
       Risk & Gap Intelligence
                  │
                  ▼
      Human-in-the-Loop Review
                  │
                  ▼
  Defensible Purchase Decision & Artifacts
  (Comparison Matrix, Executive Presentation)
```

---

## Repository Structure & Governance

This repository follows the multi-agent architecture outlined in [`.design_docs/Map.md`](.design_docs/Map.md):

```text
Procure_AI_Workspace/
├── .design_docs/
│   ├── Knowledge/         # STRICTLY READ-ONLY: Source of truth (business, architecture, UX)
│   ├── assistent/         # READ/WRITE: Multi-agent control plane, setup details, task plans
│   └── Map.md             # Repository access rules & architectural relationship
├── .venv/                 # Python virtual environment (ignored by git)
├── pyproject.toml         # Python project configuration
├── requirements.txt       # Project dependency list
├── .gitignore             # Git ignore configuration
└── README.md              # Project entry point
```

### Multi-Agent Access Policy
- **`.design_docs/Knowledge/` (READ-ONLY)**: Protected documentation for requirements, domain knowledge, agent specifications, and design artifacts. No AI coding agent should modify files in this directory.
- **`.design_docs/assistent/` (READ/WRITE)**: Central workspace for AI agents (Claude Code, OpenCode, Cursor AI, Antigravity) to maintain setup details, plans, skills, and logs.

---

## Quickstart Guide

### Prerequisites
- Python `>=3.11` (Python 3.12 recommended)
- [`uv`](https://github.com/astral-sh/uv) fast Python package manager
- `git`

### 1. Clone & Setup Repository

```powershell
git clone https://github.com/HarshithRL/procure_ai.git
cd procure_ai
```

### 2. Environment Setup with `uv`

Create and activate a virtual environment:

```powershell
# Create virtual environment
uv venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 3. Dependency Management

```powershell
# Install dependencies
uv pip install -r requirements.txt

# Add new dependency
uv add <package_name>

# Run scripts / tools
uv run python <script.py>
```

For complete command details for `uv` and `git`, see [**Setup Details & Command Guide**](.design_docs/assistent/setup_details.md).

---

## Git Remote Repository

- **Remote URL**: `https://github.com/HarshithRL/procure_ai.git`
- **Default Branch**: `main`

---

## License & Compliance

Confidential & Proprietary. All rights reserved.
