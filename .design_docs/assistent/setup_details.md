# Procure AI Workspace — Setup & Command Reference

> **Centralized Control Plane & Command Guide for AI Coding Agents & Developers**
> 
> *Targeted for Claude Code, OpenCode, Cursor AI, Antigravity, and Project Developers.*

---

## 1. Governance & Multi-Agent Collaboration

As defined in [`Map.md`](file:///d:/Work/Etex/Procure_AI_Workspace/.design_docs/Map.md):

```text
                    PROJECT
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
       /Knowledge            /assistent
            │                     │
      SOURCE OF TRUTH       CODING CONTROL PLANE
            │                     │
        READ ONLY            READ + WRITE
            │                     │
    ┌───────┼────────┐      ┌─────┼──────────────┐
    │       │        │      │     │      │       │
    ▼       ▼        ▼      ▼     ▼      ▼       ▼
  Claude OpenCode Cursor  Claude OpenCode Cursor Antigravity
   Code                    Code
```

### Agent Rules
1. **`.design_docs/Knowledge/` is STRICTLY READ-ONLY**:
   - Contains business requirements, system architecture, UX designs, and domain rules.
   - No agent may create, edit, or delete files inside `Knowledge/`.
2. **`.design_docs/assistent/` is the READ/WRITE Control Plane**:
   - Central home for agent task plans, logs, skill configs, harness scripts, and execution records.
   - Keep files cleanly organized with descriptive names and timestamped or task-based subdirectories when necessary.

---

## 2. Python & UV Environment Management

The project uses [**`uv`**](https://github.com/astral-sh/uv) for fast, reliable Python package and environment management.

### 2.1 Virtual Environment Setup

#### Create Virtual Environment
```powershell
# Create default .venv in workspace root
uv venv .venv

# Create with specific Python version
uv venv --python 3.12 .venv
```

#### Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS (Bash/Zsh)**:
  ```bash
  source .venv/bin/activate
  ```

---

### 2.2 Package Management & Dependencies

#### Install / Add Dependencies
```powershell
# Add dependencies to pyproject.toml and install
uv add <package_name>

# Add development / testing dependencies
uv add --dev pytest ruff mypy

# Install from requirements.txt
uv pip install -r requirements.txt

# Install a specific package directly into venv
uv pip install <package_name>
```

#### Sync & Lock Dependencies
```powershell
# Sync venv with pyproject.toml / uv.lock
uv sync

# Compile pyproject.toml to requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# Freeze installed packages
uv pip freeze > requirements.txt
```

#### Inspect Environment
```powershell
# List installed packages
uv pip list

# Show dependency tree
uv pip tree
```

---

### 2.3 Running Scripts & Commands with `uv`

Using `uv run` automatically executes commands within the project's virtual environment without needing manual activation:

```powershell
# Run a Python script
uv run python path/to/script.py

# Run test suite
uv run pytest

# Run linter / formatter
uv run ruff check .
uv run ruff format .

# Run interactive Python REPL
uv run python
```

---

## 3. Git Version Control Reference

**Remote Repository**: `https://github.com/HarshithRL/procure_ai.git`  
**Default Branch**: `main`

### 3.1 Initialization & Remote Setup

```powershell
# Initialize repository with default branch 'main'
git init -b main

# Add remote origin
git remote add origin https://github.com/HarshithRL/procure_ai.git

# Verify remotes
git remote -v

# Update remote URL if changed
git remote set-url origin https://github.com/HarshithRL/procure_ai.git
```

---

### 3.2 Daily Workflow Commands

#### Status & Staging
```powershell
# Check working tree status
git status

# Stage specific files
git add <file_path>

# Stage all tracked and untracked changes (respecting .gitignore)
git add .

# Unstage changes
git restore --staged <file_path>

# Discard working tree changes in a file
git restore <file_path>
```

#### Commits
```powershell
# Create a commit with a descriptive message
git commit -m "feat(module): add descriptive commit message"

# Amend the last commit without modifying message
git commit --amend --no-edit
```

#### History & Diff
```powershell
# View compact commit history with graph
git log --oneline --graph --decorate -n 20

# View unstaged diffs
git diff

# View staged diffs
git diff --staged
```

---

### 3.3 Branching & Synchronization

#### Working with Branches
```powershell
# List local branches
git branch

# List all branches (including remote)
git branch -a

# Create and switch to a new feature branch
git checkout -b feature/feature-name
# (Alternative modern syntax)
git switch -c feature/feature-name

# Switch back to main
git checkout main
# (Alternative modern syntax)
git switch main

# Delete a local branch (safe)
git branch -d feature/feature-name
```

#### Pushing & Pulling
```powershell
# Initial push to remote (sets upstream tracking)
git push -u origin main

# Standard push to current upstream branch
git push

# Fetch latest changes from all remotes
git fetch --all --prune

# Pull latest changes with rebase
git pull --rebase origin main
```

#### Stashing Work-in-Progress
```powershell
# Save local uncommitted changes to stash
git stash save "WIP: description of progress"

# List stashes
git stash list

# Restore latest stash and remove from stash list
git stash pop

# Discard top stash
git stash drop
```

---

## 4. Multi-Agent Workspace Guidelines

When working in `.design_docs/assistent/`:

1. **Naming Conventions**:
   - Use clear markdown documentation for task tracking: e.g., `task_<feature>_plan.md`, `agent_handoff_<date>.md`.
   - Store temporary execution outputs or scratch scripts in a designated `scratch/` or `logs/` subfolder.
2. **Commit Hygiene**:
   - Keep commits granular and self-contained.
   - Never commit sensitive API keys, `.env` files, or `.venv/`.
3. **Agent Handoffs**:
   - If one agent pauses work for another agent to pick up, update an agent status note in `.design_docs/assistent/` summarizing:
     - Work completed
     - Current state of the branch/files
     - Next steps and open decisions
