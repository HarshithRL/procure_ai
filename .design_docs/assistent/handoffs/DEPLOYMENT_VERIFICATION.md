# Databricks App Deployment Verification Guide

**Last Updated**: 2026-08-18  
**Status**: Ready for Validation  

---

## What Gets Deployed

### ✅ **Included in Bundle**

```
procure_ai/ (root)
├── app.py                          ✅ Flask entrypoint
├── requirements.txt                ✅ Dependencies (gunicorn, Flask, Databricks SDK)
├── web_app/                        ✅ Flask application
│   ├── __init__.py                 (app factory)
│   ├── app.yaml                    ✅ Runtime config for Databricks Apps
│   ├── auth.py                     (SSO auth handlers)
│   ├── blueprints/                 (API and view routes)
│   ├── config.py                   (Flask configuration)
│   ├── database.py                 (SQLAlchemy setup)
│   ├── models.py                   (User, Project models)
│   ├── seed.py                     (Test data)
│   ├── static/                     (CSS, JS)
│   └── templates/                  (HTML templates)
└── shared_library/                 ✅ Shared utilities
    ├── databricks_connectors/      (Platform integrations)
    ├── global_logger/              (Logging framework)
    └── model_factory/              (LLM model registry)
```

### ❌ **Excluded from Bundle**

```
.venv/                              ❌ Virtual environment
.design_docs/                       ❌ Knowledge base (read-only)
.opencode/                          ❌ AI tool config
.git/                               ❌ Version control
agent_server/                       ❌ Empty (future)
bridge/                             ❌ Empty (future)
procure_ai.db                       ❌ Local SQLite database
*.md                                ❌ Documentation (except web_app/templates)
.pytest_cache/, __pycache__/        ❌ Build artifacts
.vscode/, .idea/                    ❌ IDE config
.env, .env.local                    ❌ Secrets (use Databricks Secrets instead)
uv.lock                             ❌ Lock file
```

---

## Bundle Validation Checklist

### Step 1: Syntax & Structure

```powershell
# Validate YAML structure and path resolution
databricks bundle validate -t dev --profile DEFAULT
```

**Expected output**:
```
Validating bundle configuration in C:\path\to\Procure_AI_Workspace
✓ databricks.yml
✓ resources/ai_saas.app.yml
✓ web_app/app.yaml
✓ requirements.txt
✓ source_code_path resolution

Bundle configuration is valid.
```

**Common errors**:
- `YAML parsing error`: Check indentation in databricks.yml or resource files
- `source_code_path not found`: Verify `..` relative path in resources/ai_saas.app.yml
- `authentication failed`: Run `databricks auth login --host <URL>`

### Step 2: File Inclusion Verification

Check which files would be deployed:

```powershell
# This will show the bundle structure without uploading
databricks bundle validate --strict -t dev --profile DEFAULT
```

**What to verify**:
- ✅ `app.py` included
- ✅ `web_app/` directory included
- ✅ `shared_library/` included
- ✅ `resources/` included
- ✅ `requirements.txt` included
- ❌ `.venv/` NOT included
- ❌ `.design_docs/` NOT included
- ❌ `procure_ai.db` NOT included
- ❌ `agent_server/` NOT included
- ❌ `bridge/` NOT included

### Step 3: Deployment Dry-Run

```powershell
# Preview what bundle deploy will do (without actually deploying)
databricks bundle deploy -t dev --profile DEFAULT --dry-run
```

Expected: List of files to be uploaded to workspace.

---

## Deployment Steps

### Pre-Deployment Checklist

- [ ] Databricks CLI version ≥ 0.292.0 (`databricks --version`)
- [ ] Authenticated to workspace (`databricks auth profiles`)
- [ ] All changes committed to git (`git status` shows clean)
- [ ] requirements.txt updated with gunicorn and databricks-sdk
- [ ] web_app/app.yaml exists and has correct environment variables

### Deploy

```powershell
# Step 1: Change to repo directory
cd D:\Work\Etex\Procure_AI_Workspace

# Step 2: Validate bundle
databricks bundle validate -t dev --profile DEFAULT

# Step 3: Deploy bundle (uploads files and creates app resource)
databricks bundle deploy -t dev --profile DEFAULT

# Step 4: Start the app
databricks bundle run ai_saas -t dev --profile DEFAULT

# Step 5: Verify deployment
databricks apps get ai-saas --profile DEFAULT
databricks apps logs ai-saas --profile DEFAULT
```

---

## Post-Deployment Verification

### 1. Check App Status

```powershell
databricks apps get ai-saas --profile DEFAULT
```

**Expected output**:
```
Name: ai-saas
State: RUNNING
URL: https://adb-xxxx.cloud.databricks.com/apps/ai-saas
Created: 2026-08-18T...
Updated: 2026-08-18T...
```

### 2. Stream Logs

```powershell
databricks apps logs ai-saas --profile DEFAULT
```

**Expected log sequence**:
```
[SYSTEM] Deployment started
[SYSTEM] Uploading files...
[SYSTEM] Installing dependencies from requirements.txt
[APP] flask starting...
[APP] * Running on http://0.0.0.0:8000
[SYSTEM] Deployment successful
[APP] App started successfully
```

### 3. Access the App

1. Get URL from app status: `databricks apps get ai-saas`
2. Open URL in browser
3. You should see the login page (or redirect to `/`)
4. The X-Forwarded-User header will be injected by Databricks SSO proxy

### 4. Test Endpoints

```powershell
# Test with curl (requires token from Databricks)
# Note: Headers only present on Databricks Apps deployment, not locally

# Without Databricks auth headers (for local testing with mock):
curl -X GET http://127.0.0.1:5000/api/projects

# With Databricks SSO headers (on deployed app):
# curl -X GET https://adb-xxxx.cloud.databricks.com/apps/ai-saas/api/projects \
#   -H "Authorization: Bearer <token>"
```

### 5. Verify Seed Data

Once logged in, you should see 6 sample projects:
1. IT Infrastructure Refresh (2.4M EUR, ready)
2. Marketing Services RFP (850K EUR, ready)
3. Packaging Materials Q4 (1.2M EUR, extracting)
4. Cloud Services Migration (3.2M EUR, ready)
5. Facility Services Tender (540K EUR, draft)
6. Logistics Partnership (1.8M EUR, ready)

---

## Troubleshooting

### Issue: `resource_does_not_exist` during deploy

**Cause**: Workspace path doesn't exist or not accessible

**Fix**:
```powershell
# Check workspace root path exists
databricks workspace get-status "/Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent"

# If missing, create it
databricks workspace mkdirs "/Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent"
```

### Issue: App fails to start with `gunicorn` error

**Cause**: `gunicorn` not in requirements.txt or dependency conflict

**Fix**:
1. Verify requirements.txt includes: `gunicorn==23.0.0`
2. Check app.yaml has correct command: `["gunicorn", "app:app", ...]`
3. Redeploy: `databricks bundle deploy -t dev && databricks bundle run ai_saas -t dev`

### Issue: Database locked error

**Cause**: Multiple processes accessing `/tmp/procure_ai.db`

**Fix**:
- This is expected with SQLite (ephemeral in `/tmp`)
- Plan Lakebase migration for Sprint 2
- For now, app restarts will recreate database

### Issue: 404 on `/` route

**Cause**: Flask app not properly initialized

**Check logs**: `databricks apps logs ai-saas`

**Expected**: Logs should show Flask startup messages, not errors

### Issue: X-Forwarded headers not working

**Cause**: Testing locally or proxy not forwarding headers

**Fix**:
- X-Forwarded headers only available on deployed Databricks Apps
- Local testing: Headers must be manually added via curl `-H` flags
- See `web_app/blueprints/api.py:_get_current_user()` for handler

---

## File Size Expectations

**Expected bundle upload size**: ~500 KB - 2 MB
- app.py: < 1 KB
- web_app/: ~100-200 KB (templates, static files)
- shared_library/: ~200-500 KB
- requirements.txt: ~1 KB

**If upload is > 50 MB**: Check that `.venv/`, `__pycache__/`, or `.git/` are being excluded

---

## Rollback

If deployment fails:

```powershell
# View deployed app revision
databricks apps get ai-saas --profile DEFAULT

# Delete app (if needed)
databricks apps delete ai-saas --profile DEFAULT

# Redeploy after fixing issues
databricks bundle deploy -t dev
databricks bundle run ai_saas -t dev
```

---

## Next Steps

1. **Immediate**: Run validation steps above
2. **After deployment**: Configure permissions in Databricks UI
3. **Sprint 2**: Plan Lakebase migration for persistent storage
4. **Sprint 2**: Add SQL warehouse resource for analytics
5. **Sprint 2**: Move SECRET_KEY to Databricks Secrets

---

## References

- **Deployment Task**: `.design_docs/assistent/tasks/task_sprint1_deployment.md`
- **Handoff**: `.design_docs/assistent/handoffs/handoff_sprint1_deployment.md`
- **Workspace Config**: `.design_docs/Knowledge/Infra_and_auth_version/databricks/Workspace.md`
- **DABs Docs**: https://docs.databricks.com/dev-tools/bundles/
- **Apps Docs**: https://docs.databricks.com/dev-tools/databricks-apps/
