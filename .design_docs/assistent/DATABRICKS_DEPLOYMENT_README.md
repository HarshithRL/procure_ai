# Databricks App Deployment Setup — Complete Reference

**Status**: ✅ Ready for Deployment  
**Date**: 2026-08-18  
**Commits**: 
- `8be5685` - Initial DAB and app configuration
- `462dfa7` - Add exclude_patterns to filter deployment files
- `1b09892` - Add verification guide and quick checklist

---

## Overview

The Procure AI repository is fully configured to deploy as a managed Databricks App using Declarative Automation Bundles (DABs). This document is your complete reference for understanding what gets deployed, how to deploy it, and how to verify it works.

---

## What Gets Deployed

### ✅ Production Code (Included)

```
procure_ai/
├── app.py                          ← Flask entrypoint for gunicorn
├── requirements.txt                ← Python dependencies
├── web_app/                        ← Flask application
│   ├── __init__.py                 (factory)
│   ├── app.yaml                    (Databricks runtime config)
│   ├── auth.py                     (X-Forwarded SSO auth)
│   ├── blueprints/api.py           (REST API endpoints)
│   ├── blueprints/views.py         (HTML view routes)
│   ├── config.py                   (Flask configuration)
│   ├── database.py                 (SQLAlchemy setup)
│   ├── models.py                   (User, Project models)
│   ├── seed.py                     (Test data generation)
│   ├── static/                     (CSS, JS, images)
│   └── templates/                  (HTML templates)
└── shared_library/                 ← Shared utilities
    ├── databricks_connectors/      (Workspace integrations)
    ├── global_logger/              (Logging framework)
    ├── model_factory/              (LLM registry)
    └── utilities/                  (Helpers)
```

**Total size**: ~500 KB - 2 MB (varies by static assets)

### ❌ Excluded (NOT Deployed)

```
.venv/                              (Virtual environment)
.design_docs/                       (Knowledge base — read-only)
.opencode/                          (AI tool configuration)
.git/                               (Version control)
agent_server/                       (Empty, future Sprint 2+)
bridge/                             (Empty, future Sprint 2+)
procure_ai.db                       (Local SQLite, recreated per deployment)
*.md files                          (Documentation)
__pycache__/, .pytest_cache/        (Build artifacts)
.vscode/, .idea/                    (IDE configuration)
.env files                          (Secrets — use Databricks instead)
uv.lock                             (Lock file)
```

---

## Repository Structure for Deployment

### DAB Configuration Files

```yaml
# databricks.yml (root)
# Main bundle configuration with targets and exclusions
bundle:
  name: procure-ai
  include:
    - resources/*.yml
  exclude_patterns:
    - .venv/
    - .design_docs/
    - agent_server/
    - bridge/
    - procure_ai.db
    # ... (see full file for complete list)
targets:
  dev:
    workspace:
      host: https://adb-7181820732839861.1.azuredatabricks.net/
      root_path: /Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent
  prod:
    workspace:
      host: https://adb-7181820732839861.1.azuredatabricks.net/
      root_path: /Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent
```

```yaml
# resources/ai_saas.app.yml
# App resource definition
resources:
  apps:
    ai_saas:
      name: ai-saas
      description: Procure AI application
      source_code_path: ..
```

```yaml
# web_app/app.yaml
# Databricks App runtime configuration
command:
  - gunicorn
  - app:app
  - -w 4
  - -b 0.0.0.0:8000
env:
  - name: FLASK_ENV
    value: production
  - name: DATABASE_URL
    value: sqlite:////tmp/procure_ai.db
```

---

## How Deployment Works

### 1. Bundle Structure

Databricks DABs organizes resources declaratively:
- **databricks.yml**: Main config with targets and variables
- **resources/**: Resource definition files (jobs, pipelines, apps, etc.)
- **src/**: Application source code (in our case, root level)

### 2. Exclusion Pattern Matching

When you run `databricks bundle deploy`:
1. Reads `exclude_patterns` from databricks.yml
2. Ignores matching files and directories
3. Uploads remaining files to workspace
4. Runs deployment for each resource

**Our exclude_patterns ensures**:
- ✅ Core app code uploaded (app.py, web_app/, shared_library/)
- ✅ Dependencies declared (requirements.txt)
- ✅ No large build artifacts uploaded (.venv/, __pycache__)
- ✅ No local data persisted (procure_ai.db)
- ✅ No development files (IDE config, .design_docs/)

### 3. App Startup

Once deployed, Databricks Apps:
1. Creates a container with Python 3.11 runtime
2. Installs dependencies: `pip install -r requirements.txt`
3. Runs app.yaml command: `gunicorn app:app -w 4 -b 0.0.0.0:8000`
4. Forwards incoming requests to Flask app
5. Injects X-Forwarded-User header for SSO auth

---

## Deployment Workflow

### Pre-Deployment Checks

```powershell
# 1. Verify CLI version
databricks --version
# Expected: 0.292.0 or higher

# 2. List authenticated profiles
databricks auth profiles
# Expected: See workspace profile (typically "DEFAULT")

# 3. Test connectivity
databricks workspace list / --profile DEFAULT
# Expected: No errors
```

### Deployment Commands

```powershell
# Navigate to repo root
cd D:\Work\Etex\Procure_AI_Workspace

# Step 1: Validate bundle structure
databricks bundle validate -t dev --profile DEFAULT

# Step 2: Deploy (upload source, create resources)
databricks bundle deploy -t dev --profile DEFAULT

# Step 3: Start the app (required first time and after redeploy)
databricks bundle run ai_saas -t dev --profile DEFAULT

# Step 4: Check status
databricks apps get ai-saas --profile DEFAULT

# Step 5: Stream logs
databricks apps logs ai-saas --profile DEFAULT
```

### Expected Output

**Validate**:
```
Validating bundle configuration in D:\Work\Etex\Procure_AI_Workspace
✓ databricks.yml
✓ resources/ai_saas.app.yml
✓ web_app/app.yaml

Bundle configuration is valid.
```

**Deploy**:
```
Uploading files...
Workspace: https://adb-7181820732839861.1.azuredatabricks.net/
Files to upload: ~50
Uploading...
✓ 100% complete

Deploying resources...
✓ App resource 'ai_saas' created/updated

Deployment completed successfully.
```

**Logs** (first startup):
```
[SYSTEM] Deployment started
[SYSTEM] Installing dependencies from requirements.txt
[SYSTEM] flask 3.1.3 installed
[SYSTEM] gunicorn 23.0.0 installed
[APP] Starting gunicorn...
[APP] * Running on http://0.0.0.0:8000
[APP] Worker processes: 4
[SYSTEM] Deployment successful
[APP] Listening for requests
```

---

## Verification Checklist

### Deployment Successful If

- ✅ `databricks bundle validate` completes without errors
- ✅ `databricks bundle deploy` uploads files and creates app resource
- ✅ `databricks apps get ai-saas` shows `State: RUNNING`
- ✅ App URL is accessible and loads
- ✅ `databricks apps logs ai-saas` shows startup messages, no errors
- ✅ Seed data (6 projects) visible in app UI

### Testing the Deployment

```powershell
# Get the app URL
$app = databricks apps get ai-saas --profile DEFAULT
Write-Output $app.url

# Test API endpoints (assuming deployed)
# Open URL in browser and test login flow
# Verify X-Forwarded-User header auth works
```

---

## Important Notes

### Database Behavior

**Sprint 1 (Current)**:
- Uses SQLite at `/tmp/procure_ai.db` (ephemeral)
- Database recreated on every app restart
- Seed data reloads automatically
- Acceptable for MVP and testing

**Sprint 2+ (Planned)**:
- Migrate to Lakebase PostgreSQL (`ds-vendor-agent` project)
- Update `DATABASE_URL` env var in app.yaml
- Add `psycopg2-binary` to requirements.txt
- Persistent user and project data across restarts

### Authentication

**How It Works**:
1. App is deployed to Databricks Apps platform
2. Databricks injects `X-Forwarded-User`, `X-Forwarded-Email` headers
3. Flask extracts headers via `web_app/blueprints/api.py:_get_current_user()`
4. Auto-provisions new users on first login
5. Existing users validated against database

**Important**: X-Forwarded headers only available on deployed apps, not local testing

### Secrets Management

**Current (Not Secure)**:
- `SECRET_KEY` hardcoded in app.yaml

**TODO (Sprint 1 or 2)**:
```powershell
# Create secret in Databricks
databricks secrets put --scope procurement --key flask-secret-key

# Update app.yaml
env:
  - name: SECRET_KEY
    valueFrom: secret-key
```

---

## File Reference

### Configuration Files Created

| File | Purpose | Status |
|------|---------|--------|
| `app.py` | Flask entrypoint for gunicorn | ✅ Ready |
| `databricks.yml` | DAB bundle config with exclusions | ✅ Ready |
| `web_app/app.yaml` | Databricks App runtime config | ✅ Ready |
| `resources/ai_saas.app.yml` | App resource definition | ✅ Ready |
| `requirements.txt` | Dependencies (gunicorn, Flask, etc.) | ✅ Ready |
| `web_app/config.py` | Updated for /tmp database in prod | ✅ Ready |

### Documentation Created

| Document | Location | Purpose |
|----------|----------|---------|
| Deployment Task | `.design_docs/assistent/tasks/task_sprint1_deployment.md` | Complete deployment guide |
| Handoff Notes | `.design_docs/assistent/handoffs/handoff_sprint1_deployment.md` | Status and next steps |
| Verification Guide | `.design_docs/assistent/handoffs/DEPLOYMENT_VERIFICATION.md` | Detailed validation steps |
| Quick Checklist | `.design_docs/assistent/DEPLOYMENT_CHECKLIST.md` | Copy-paste deployment commands |

---

## Troubleshooting

### Common Issues

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| `bundle validation fails` | YAML syntax error | Run `databricks bundle validate --strict` for details |
| `resource_does_not_exist` | Workspace path inaccessible | Create path: `databricks workspace mkdirs /Workspace/Users/...` |
| `gunicorn: command not found` | gunicorn not in requirements.txt | Add `gunicorn==23.0.0` to requirements.txt, redeploy |
| `app won't start` | Check logs for startup errors | `databricks apps logs ai-saas` |
| `database locked error` | SQLite contention in /tmp | Expected for Sprint 1; plan Lakebase migration |
| `X-Forwarded headers missing` | Testing locally | Headers only on deployed app; manually add for local testing |

### Debug Commands

```powershell
# Validate with full error details
databricks bundle validate --strict -t dev

# Check workspace connectivity
databricks workspace get-status /Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent

# View deployed app details
databricks apps get ai-saas

# Stream live logs (press Ctrl+C to exit)
databricks apps logs ai-saas --follow

# Delete app (if needed for reset)
databricks apps delete ai-saas
```

---

## Next Steps

### Immediate (After Deployment)

1. ✅ Run deployment commands above
2. ✅ Verify app is running and accessible
3. ✅ Test login flow and see seed data
4. ✅ Configure app permissions (Databricks UI)

### Sprint 2 (Planned)

- [ ] Migrate database to Lakebase PostgreSQL
- [ ] Move SECRET_KEY to Databricks Secrets
- [ ] Add SQL warehouse resource for analytics
- [ ] Add Vector Search index for semantic search
- [ ] Implement chat agent integration

---

## Key Contacts & Resources

**Workspace**: https://adb-7181820732839861.1.azuredatabricks.net/  
**App Name**: `ai-saas`  
**Workspace Path**: `/Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent`  

**Official Documentation**:
- [Databricks Apps](https://docs.databricks.com/dev-tools/databricks-apps/)
- [Declarative Automation Bundles (DABs)](https://docs.databricks.com/dev-tools/bundles/)
- [CLI Reference](https://docs.databricks.com/dev-tools/cli/)

**Internal Documentation**:
- [Workspace Configuration](../../Knowledge/Infra_and_auth_version/databricks/Workspace.md)
- [Agent Governance](../../../AGENTS.md)
- [Setup Details](./setup_details.md)

---

## Summary

You have everything needed to deploy Procure AI to Databricks Apps:

✅ **Configuration**: databricks.yml, app.yaml, requirements.txt  
✅ **Application Code**: Flask app with auth, models, and seed data  
✅ **Documentation**: Full deployment guides and checklists  
✅ **Filtering**: Exclude patterns prevent unnecessary files from uploading  

**Next action**: Run `databricks bundle validate -t dev` to begin deployment.

Good luck! 🚀
