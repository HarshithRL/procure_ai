# Sprint 1 Deployment Task — Databricks App Setup

**Status**: ✅ Configuration Complete  
**Date**: 2026-08-18  
**Owner**: OpenCode Agent  

---

## Summary

The repository has been structured for deployment to Databricks Apps using Declarative Automation Bundles (DABs). All core configuration files are in place to deploy the Procure AI Flask application as a managed Databricks App.

---

## What Was Done

### 1. Created Flask Entrypoint (`app.py`)
- **File**: `D:\Work\Etex\Procure_AI_Workspace\app.py`
- **Purpose**: Gunicorn-compatible entrypoint that exports the Flask app
- **Usage**: Gunicorn runs `app:app` to load and run the application
- **Environment variables**:
  - `FLASK_ENV`: "development" or "production"
  - `DATABASE_URL`: SQLAlchemy connection string (default: SQLite in `/tmp`)
  - `SECRET_KEY`: Flask session secret (auto-generated for security)

### 2. Created Databricks App Config (`web_app/app.yaml`)
- **File**: `D:\Work\Etex\Procure_AI_Workspace\web_app\app.yaml`
- **Purpose**: Runtime configuration for Databricks Apps platform
- **Command**: Runs gunicorn with 4 workers, bound to `0.0.0.0:8000`
- **Database**: Uses SQLite in `/tmp` (ephemeral, reseeds on restart with idempotent seed data)
- **Environment**:
  - `FLASK_ENV=production`
  - `DATABASE_URL=sqlite:////tmp/procure_ai.db`
  - `SECRET_KEY` placeholder (upgrade to Databricks secret in production)

### 3. Created DAB Bundle Config (`databricks.yml`)
- **File**: `D:\Work\Etex\Procure_AI_Workspace\databricks.yml`
- **Purpose**: Main Declarative Automation Bundle configuration
- **Targets**: `dev` (default) and `prod` environments
- **Workspace**: Points to production Databricks workspace
  - **Host**: `https://adb-7181820732839861.1.azuredatabricks.net/`
  - **Root Path**: `/Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent`
- **Includes**: All resource files from `resources/` directory

### 4. Created App Resource Definition (`resources/ai_saas.app.yml`)
- **File**: `D:\Work\Etex\Procure_AI_Workspace\resources\ai_saas.app.yml`
- **Purpose**: Defines the `ai-saas` app resource for deployment
- **App Name**: `ai-saas` (matches target Databricks app from `Workspace.md`)
- **Source Path**: Points to bundle root (contains `app.py` and `web_app/`)

### 5. Updated Requirements (`requirements.txt`)
- **File**: `D:\Work\Etex\Procure_AI_Workspace\requirements.txt`
- **Dependencies**:
  - `flask>=3.1.3`, `flask-cors>=6.0.5` — Web framework
  - `sqlalchemy>=2.0.52` — ORM
  - `gunicorn>=23.0.0` — Application server (required for deployment)
  - `databricks-sdk>=0.30.0` — Databricks integration
  - `python-dotenv>=1.0.0` — Environment variable management

### 6. Updated `.gitignore`
- Added explicit `procure_ai.db` entry to exclude local development database
- (Already covered by `*.db` but now explicit for clarity)

---

## Deployment Instructions

### Prerequisites

1. **Databricks CLI**: Must be installed and authenticated
   ```powershell
   databricks --version
   databricks auth profiles
   ```

2. **Git**: Commit all changes before deployment
   ```powershell
   git status
   git add .
   git commit -m "feat(deployment): add DABs configuration for Databricks App"
   git push origin main
   ```

### Deploy to Dev Environment

```powershell
# Validate bundle configuration
databricks bundle validate -t dev --profile DEFAULT

# Deploy (uploads source and creates/updates app resource)
databricks bundle deploy -t dev --profile DEFAULT

# Start the app (required after first deploy)
databricks bundle run ai_saas -t dev --profile DEFAULT
```

### Check Status

```powershell
# View app status and URL
databricks apps get ai-saas --profile DEFAULT

# Stream live logs
databricks apps logs ai-saas --profile DEFAULT

# Access the app
# Open URL returned by `databricks apps get ai-saas`
```

### Deploy to Production

```powershell
# Validate for prod
databricks bundle validate -t prod --profile DEFAULT

# Deploy to prod
databricks bundle deploy -t prod --profile DEFAULT

# Start prod app
databricks bundle run ai_saas -t prod --profile DEFAULT
```

---

## Architecture

### Repo Structure

```
procure_ai/
├── app.py                          # Flask entrypoint (for gunicorn)
├── databricks.yml                  # DAB bundle config
├── resources/
│   └── ai_saas.app.yml             # App resource definition
├── web_app/
│   ├── app.yaml                    # Databricks App runtime config
│   ├── __init__.py                 # Flask app factory
│   ├── auth.py                     # X-Forwarded header auth
│   ├── blueprints/
│   │   ├── api.py                  # REST API endpoints
│   │   └── views.py                # View routes (HTML)
│   ├── config.py                   # Flask configuration
│   ├── database.py                 # SQLAlchemy setup
│   ├── models.py                   # User and Project models
│   ├── seed.py                     # Database seeding
│   ├── static/                     # CSS, JS, images
│   └── templates/                  # HTML templates
├── agent_server/                   # (Empty, future agent backend)
├── bridge/                         # (Empty, future bridge layer)
├── shared_library/                 # Shared utilities and connectors
├── requirements.txt                # Runtime dependencies
└── pyproject.toml                  # Project metadata
```

### Data Persistence

**Current (Sprint 1)**: SQLite in `/tmp`
- Location: `/tmp/procure_ai.db` (ephemeral)
- Seed data reloads on app restart (idempotent)
- Acceptable for Sprint 1 since Databricks Apps are stateless

**Future (Sprint 2)**: Lakebase (Postgres)
- Use `ds-vendor-agent` project from `Workspace.md:10`
- Update `DATABASE_URL` to PostgreSQL connection string
- Add `psycopg2-binary` to requirements
- Enables persistent user and project data across restarts

### Authentication

**X-Forwarded Headers**: Extracted by `web_app/blueprints/api.py:_get_current_user()`
- Headers injected by Databricks SSO proxy when app is deployed
- Auto-provisions users on first login
- Headers: `X-Forwarded-Email`, `X-Forwarded-User`, `X-Forwarded-Preferred-Username`

---

## Resource Permissions (TODO)

After deployment, configure app permissions in Databricks UI:

1. Navigate to **Apps** → **ai-saas**
2. Click **Permissions**
3. Grant **CAN USE** to procurement team users/groups
4. Grant **CAN MANAGE** only to app developers

---

## Deployment Checklist

- [x] Flask entrypoint created (`app.py`)
- [x] Databricks App config created (`web_app/app.yaml`)
- [x] DAB bundle config created (`databricks.yml`)
- [x] App resource defined (`resources/ai_saas.app.yml`)
- [x] Requirements updated with gunicorn and Databricks SDK
- [x] `.gitignore` updated
- [ ] Bundle validated (`databricks bundle validate -t dev`)
- [ ] Bundle deployed (`databricks bundle deploy -t dev`)
- [ ] App started (`databricks bundle run ai_saas -t dev`)
- [ ] App permissions configured (Databricks UI)
- [ ] Team notified of app URL and access

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Bundle validation fails** | Run `databricks bundle validate -t dev` to see detailed errors. Check workspace connectivity. |
| **Auth token not found** | CLI needs OAuth. Re-authenticate: `databricks auth login --host <URL>` |
| **App won't start** | Check logs: `databricks apps logs ai-saas`. Common: missing deps in requirements.txt, wrong gunicorn command. |
| **Database locked error** | SQLite contention in `/tmp`. Plan Lakebase migration for Sprint 2. |
| **X-Forwarded headers missing** | App only receives headers when deployed on Databricks Apps. Test locally with curl `-H` flags. |

---

## Next Steps

1. **Immediate**: Test bundle locally with `databricks bundle validate -t dev`
2. **Next**: Deploy to dev environment and verify logs
3. **Sprint 2**: Plan Lakebase migration for persistent user/project storage
4. **Sprint 2**: Add SQL warehouse resource for analytics queries
5. **Sprint 2**: Configure Databricks secrets for sensitive env vars (SECRET_KEY)

---

## References

- **Databricks Apps Docs**: https://docs.databricks.com/dev-tools/databricks-apps/
- **DABs Docs**: https://docs.databricks.com/dev-tools/bundles/
- **Workspace Configuration**: `.design_docs/Knowledge/Infra_and_auth_version/databricks/Workspace.md`
- **Agent Governance**: `AGENTS.md` (Sections 1–7)
