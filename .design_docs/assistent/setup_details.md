# Procure AI Workspace — Setup & Command Reference

> **Centralized Control Plane & Master Command Guide for AI Coding Agents & Developers**
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

### 1.1 Strict Access Rules
1. **`.design_docs/Knowledge/` is STRICTLY READ-ONLY**:
   - Contains business requirements, system architecture, UX designs, and domain rules.
   - **No agent may create, edit, or delete files inside `Knowledge/`**.
2. **`.design_docs/assistent/` is the READ/WRITE Control Plane**:
   - Central repository for agent task plans, logs, skill configs, harness scripts, and execution records.
   - Keep files cleanly organized with descriptive names and task-based subdirectories.

### 1.2 Multi-Agent Workspace Organization
```text
.design_docs/assistent/
├── setup_details.md          # This master command & environment reference
├── tasks/                    # Active and completed task plans (e.g. task_sprint1_ui.md)
├── handoffs/                 # Inter-agent status logs and handoff notes
└── scratch/                  # Temporary debug logs and one-off agent notes
```

---

## 2. Python & UV Environment Management

The project uses [**`uv`**](https://github.com/astral-sh/uv) for fast, reliable Python package and environment management.

### 2.1 Virtual Environment Setup

#### Create & Manage Virtual Environment
```powershell
# Create default .venv in workspace root
uv venv .venv

# Create with specific Python version
uv venv --python 3.12 .venv

# Pin project Python version
uv python pin 3.12
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

#### Adding & Removing Dependencies
```powershell
# Add dependency to pyproject.toml and install
uv add <package_name>

# Add development / test dependency
uv add --dev pytest ruff mypy

# Remove a dependency
uv remove <package_name>

# Install all dependencies from requirements.txt
uv pip install -r requirements.txt

# Install a specific package directly into venv
uv pip install <package_name>
```

#### Syncing & Lockfiles
```powershell
# Generate / update lockfile
uv lock

# Sync venv exactly to match pyproject.toml / uv.lock
uv sync

# Sync without updating lockfile (frozen)
uv sync --frozen

# Compile pyproject.toml to requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# Freeze current environment packages to requirements.txt
uv pip freeze > requirements.txt
```

#### Inspecting Packages
```powershell
# List installed packages
uv pip list

# View package dependency tree
uv pip tree
```

---

### 2.3 Running Scripts, Tests & Tools with `uv`

`uv run` automatically executes commands inside the virtual environment without requiring manual activation:

```powershell
# Execute a Python script
uv run python path/to/script.py

# Run test suite
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Lint and format code with Ruff
uv run ruff check .
uv run ruff check . --fix
uv run ruff format .

# Type checking with MyPy
uv run mypy src/

# Run interactive Python REPL
uv run python
```

---

## 3. UI, Web App & Databricks Execution

Commands for running, developing, testing, and deploying the application UI and backend services.

### 3.1 Flask / Backend Development Server

```powershell
# Run Flask dev server with hot reload
uv run flask --app app run --debug --port 5000

# Run Flask on all interfaces (for remote / container testing)
uv run flask --app app run --host=0.0.0.0 --port 5000

# Run with Gunicorn (Production WSGI)
uv run gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# Run with Uvicorn (if ASGI / FastAPI endpoints are used)
uv run uvicorn app:asgi_app --reload --port 8000
```

---

### 3.2 Frontend & UI Build Commands (Node / npm / Vite)

If developing dedicated frontend client components or SPA dashboards:

```powershell
# Install frontend dependencies
npm install

# Start local frontend development server (with hot module replacement)
npm run dev

# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview

# Run frontend tests
npm test

# Lint frontend code
npm run lint
```

---

### 3.3 Databricks Apps & SSO Integration

Sprint 1 targets deployment to **Databricks Apps** with SSO header integration:

#### Databricks CLI App Management
```powershell
# Authenticate Databricks CLI
databricks auth login --host https://<databricks-instance-url>

# List deployed Databricks apps
databricks apps list

# Create a new Databricks app
databricks apps create procure-ai-workspace

# Deploy local source code to Databricks App
databricks apps deploy procure-ai-workspace --source-code-path .

# Get app status and URL
databricks apps get procure-ai-workspace

# View live runtime logs
databricks apps logs procure-ai-workspace --follow

# Stop or restart app
databricks apps stop procure-ai-workspace
databricks apps start procure-ai-workspace
```

#### Simulating Databricks SSO & Proxy Headers Locally
Databricks Apps inject proxy headers for authenticated users. Simulate them during local testing using `curl`:

```powershell
# Test local endpoint with simulated Databricks SSO headers
curl -X GET http://127.0.0.1:5000/api/profile `
  -H "X-Forwarded-User: user@company.com" `
  -H "X-Forwarded-Email: user@company.com" `
  -H "X-Forwarded-Preferred-Username: Jane Doe"
```

---

## 4. Master Git Version Control Reference

**Remote Repository**: `https://github.com/HarshithRL/procure_ai.git`  
**Default Branch**: `main`

---

### 4.1 Git Configuration & Remotes

```powershell
# Configure local user identity
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Check remotes
git remote -v

# Add remote origin
git remote add origin https://github.com/HarshithRL/procure_ai.git

# Update remote URL
git remote set-url origin https://github.com/HarshithRL/procure_ai.git

# Show detailed remote information
git remote show origin

# Prune stale remote tracking branches
git remote prune origin
```

---

### 4.2 Status, Staging & Commits

```powershell
# Check compact status
git status -sb

# Stage specific file or directory
git add path/to/file

# Interactive staging (stage hunks)
git add -p

# Stage all tracked & untracked changes (respecting .gitignore)
git add .

# Create commit with message
git commit -m "feat(scope): concise description of changes"

# Commit all tracked modifications directly
git commit -am "fix(auth): resolve x-forwarded header parsing"

# Amend the last commit without changing message
git commit --amend --no-edit

# Amend the last commit with new message
git commit --amend -m "chore: updated commit message"
```

---

### 4.3 Viewing Diff & History

```powershell
# Compact log with ASCII graph, branch names, and commit hashes
git log --graph --oneline --decorate --all -n 25

# Log showing files changed in each commit
git log --stat -n 10

# Search commit history by commit message
git log --grep="sprint 1"

# Search commit history by code change
git log -S "def extract_requirements"

# View unstaged changes in working tree
git diff

# View staged changes (ready to commit)
git diff --staged

# Compare two branches
git diff main..feature/chat-agent

# Inspect a specific commit
git show <commit_hash>
```

---

### 4.4 Branch Management & Workflow

```powershell
# List local branches
git branch

# List all branches (local and remote)
git branch -a -vv

# Create and switch to a new branch
git switch -c feature/sprint1-flask-app
# (Traditional syntax)
git checkout -b feature/sprint1-flask-app

# Switch to an existing branch
git switch main
# (Traditional syntax)
git checkout main

# Rename current branch
git branch -m new-branch-name

# Delete a merged local branch
git branch -d feature/sprint1-flask-app

# Force delete an unmerged local branch
git branch -D feature/sprint1-flask-app

# Delete a remote branch
git push origin --delete feature/sprint1-flask-app
```

---

### 4.5 Syncing, Pulling & Pushing

```powershell
# Fetch all branches and tags from remote (without merging)
git fetch --all --prune

# Push new branch to remote and set upstream tracking
git push -u origin feature/sprint1-flask-app

# Standard push to current upstream
git push

# Pull latest changes from upstream using rebase (maintains clean linear history)
git pull --rebase origin main

# Standard pull (with merge commit)
git pull origin main

# Safe force push after rebase (never use bare --force in shared repos)
git push --force-with-lease
```

---

### 4.6 Merging, Rebasing & Cherry-Picking

```powershell
# Merge a feature branch into the current branch (creating a merge commit)
git merge feature/sprint1-flask-app --no-ff -m "merge: integrate sprint 1 flask app"

# Rebase current branch on top of main
git rebase main

# Interactive rebase (squash / edit / reorder last N commits)
git rebase -i HEAD~4

# Apply a specific commit from another branch onto current branch
git cherry-pick <commit_hash>

# Abort an in-progress merge
git merge --abort

# Abort an in-progress rebase
git rebase --abort
```

---

### 4.7 Conflict Resolution Workflow

When a merge or rebase encounters conflicts:

1. **Identify conflicted files**:
   ```powershell
   git status
   ```
2. **Open conflicting files and inspect conflict markers**:
   ```text
   <<<<<<< HEAD
   current branch changes
   =======
   incoming branch changes
   >>>>>>> branch-or-commit
   ```
3. **Edit file to keep desired code, remove conflict markers, and save**.
4. **Mark resolved**:
   ```powershell
   git add <resolved_file>
   ```
5. **Continue process**:
   - For rebase: `git rebase --continue`
   - For merge: `git commit -m "resolve merge conflicts"`
6. **If you need to cancel**:
   ```powershell
   git rebase --abort
   # or
   git merge --abort
   ```

---

### 4.8 Undo, Reset & Rollback Safely

```powershell
# Discard unstaged modifications in a file
git restore <file_path>

# Unstage a file (keep changes in working directory)
git restore --staged <file_path>

# Revert a published commit by creating a new inverse commit (Safe for shared repos)
git revert <commit_hash>

# Undo the last commit but KEEP all changes staged
git reset --soft HEAD~1

# Undo the last commit and UNSTAGE changes (keep in working directory)
git reset HEAD~1

# HARD RESET: Discard last commit and all working directory changes (DESTRUCTIVE)
git reset --hard HEAD~1

# Clean untracked files (Dry run - shows what will be deleted)
git clean -fdn

# Clean untracked files & directories (Actually delete)
git clean -fd
```

---

### 4.9 Stash Management (Work-in-Progress)

```powershell
# Stash tracked & untracked changes with a descriptive message
git stash push -u -m "WIP: sprint 1 chat context management"

# View list of stashed changes
git stash list

# View diff of a specific stash
git stash show -p stash@{0}

# Apply latest stash and remove it from stash list
git stash pop

# Apply latest stash and KEEP it in stash list
git stash apply

# Apply a specific stash from list
git stash apply stash@{1}

# Delete a specific stash
git stash drop stash@{0}

# Clear all stashes
git stash clear
```

---

### 4.10 Releases & Tagging

```powershell
# Create an annotated release tag
git tag -a v0.1.0 -m "Release v0.1.0 - Sprint 1 Databricks App & Chat MVP"

# List all tags
git tag -l

# View tag details
git show v0.1.0

# Push a specific tag to remote
git push origin v0.1.0

# Push all local tags to remote
git push origin --tags

# Delete a local tag
git tag -d v0.1.0

# Delete a remote tag
git push origin --delete v0.1.0
```

---

## 5. Summary Cheat Sheet for Developers & Agents

| Task | Command |
| :--- | :--- |
| **Create & Activate Env** | `uv venv .venv` → `.venv\Scripts\Activate.ps1` |
| **Run Python Script / App** | `uv run python <script.py>` or `uv run flask --app app run --debug` |
| **Add / Remove Package** | `uv add <pkg>` / `uv remove <pkg>` |
| **Sync Virtual Env** | `uv sync` |
| **Run Unit Tests** | `uv run pytest` |
| **Lint & Format** | `uv run ruff check . --fix` && `uv run ruff format .` |
| **Frontend Dev Server** | `npm run dev` |
| **Frontend Build** | `npm run build` |
| **Databricks App Deploy** | `databricks apps deploy procure-ai-workspace --source-code-path .` |
| **Check Git Status** | `git status -sb` |
| **Create & Switch Branch** | `git switch -c feature/<name>` |
| **Pull with Rebase** | `git pull --rebase origin main` |
| **Stage & Commit** | `git add .` → `git commit -m "feat: description"` |
| **Push Branch** | `git push -u origin <branch>` |
| **View Clean Git Log** | `git log --graph --oneline --decorate -n 20` |
