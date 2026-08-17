# Databricks App Deployment — Quick Checklist

**Date**: 2026-08-18  
**App Name**: `ai-saas`  
**Workspace**: https://adb-7181820732839861.1.azuredatabricks.net/  

---

## Pre-Deployment (Do These First)

- [ ] **CLI Ready**: `databricks --version` shows v0.292.0 or higher
- [ ] **Authenticated**: `databricks auth profiles` shows workspace profile
- [ ] **Git Clean**: `git status` shows no uncommitted changes
- [ ] **Files Created**:
  - [ ] `app.py` (root)
  - [ ] `databricks.yml` (root)
  - [ ] `web_app/app.yaml`
  - [ ] `resources/ai_saas.app.yml`
  - [ ] `requirements.txt` (updated with gunicorn, databricks-sdk)
- [ ] **Configs Correct**:
  - [ ] app.yaml command: `["gunicorn", "app:app", "-w", "4", "-b", "0.0.0.0:8000"]`
  - [ ] app.yaml env vars: FLASK_ENV, DATABASE_URL, SECRET_KEY
  - [ ] databricks.yml targets: dev, prod
  - [ ] databricks.yml exclude_patterns: agent_server/, bridge/, procure_ai.db, .venv/, etc.

---

## Deployment (Copy/Paste These Commands)

```powershell
# Navigate to repo root
cd D:\Work\Etex\Procure_AI_Workspace

# Step 1: Validate bundle structure and exclusions
databricks bundle validate -t dev --profile DEFAULT

# Step 2: Deploy (uploads source and creates app resource)
databricks bundle deploy -t dev --profile DEFAULT

# Step 3: Start the app (required first time)
databricks bundle run ai_saas -t dev --profile DEFAULT
```

---

## Post-Deployment (Verify These)

- [ ] **App Running**: `databricks apps get ai-saas --profile DEFAULT` shows `State: RUNNING`
- [ ] **URL Accessible**: Copy URL from above, open in browser
- [ ] **Logs Clean**: `databricks apps logs ai-saas --profile DEFAULT` shows no errors
- [ ] **Database Created**: App should auto-create `/tmp/procure_ai.db` with seed data
- [ ] **Seed Data Present**: 6 sample projects should be visible in app UI

---

## Key Files Deployed

```
✅ app.py                      — Flask entrypoint
✅ web_app/                    — Flask application code
✅ web_app/app.yaml            — Databricks runtime config
✅ shared_library/             — Shared modules
✅ requirements.txt            — Dependencies
```

## Key Files NOT Deployed

```
❌ .venv/                      — Virtual environment
❌ .design_docs/               — Knowledge base
❌ .git/                       — Version control
❌ agent_server/               — Empty (future)
❌ bridge/                     — Empty (future)
❌ procure_ai.db               — Local database
❌ *.md files                  — Documentation
```

---

## Troubleshooting Quick Links

| Problem | Command |
|---------|---------|
| Bundle won't validate | `databricks bundle validate --strict -t dev` |
| App won't start | `databricks apps logs ai-saas` |
| Need app URL | `databricks apps get ai-saas` |
| Need to delete app | `databricks apps delete ai-saas` |
| Need to redeploy | Run Deploy step 2 & 3 above |

---

## Success Indicators

✅ **Valid**: `databricks bundle validate` completes without errors  
✅ **Deployed**: `databricks bundle deploy` shows upload progress  
✅ **Running**: `databricks apps get ai-saas` shows `State: RUNNING`  
✅ **Accessible**: Can open app URL in browser  
✅ **Logs**: `databricks apps logs ai-saas` shows startup messages, no errors  
✅ **Data**: See 6 sample projects in UI after login  

---

## After Deployment

1. **Configure Permissions** (Databricks UI):
   - App → Permissions → Grant "CAN USE" to team, "CAN MANAGE" to admins

2. **Plan Sprint 2**:
   - Migrate SQLite → Lakebase PostgreSQL
   - Move SECRET_KEY to Databricks Secrets
   - Add SQL warehouse resource
   - Add Vector Search for semantic search

3. **Notify Team**:
   - Share app URL
   - Explain X-Forwarded SSO auth (automatic)
   - Document test projects and workflows

---

## Handy References

- **Full Deployment Guide**: `.design_docs/assistent/handoffs/handoff_sprint1_deployment.md`
- **Verification Steps**: `.design_docs/assistent/handoffs/DEPLOYMENT_VERIFICATION.md`
- **Workspace Config**: `.design_docs/Knowledge/Infra_and_auth_version/databricks/Workspace.md`
- **DABs Docs**: https://docs.databricks.com/dev-tools/bundles/
- **Apps Docs**: https://docs.databricks.com/dev-tools/databricks-apps/

---

**Ready to deploy?** Follow the "Deployment" section above. Good luck! 🚀
