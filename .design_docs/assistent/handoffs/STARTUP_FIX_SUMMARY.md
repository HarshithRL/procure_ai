# Procure AI Startup Fix Summary

**Date**: 2026-08-18  
**Status**: ✅ Resolved  
**Severity**: Critical (Production Deployment Blocker)

---

## Problem

Databricks App deployment failed with a **`KeyError: 'ENV'`** during Flask app initialization.

### Error Trace
```
File "/app/python/source_code/wsgi.py", line 67, in <module>
    logger.info(f"Flask app created | env={flask_env} | config={app.config['ENV']}")
                                                                ~~~~~~~~~~^^^^^^^
KeyError: 'ENV'
```

### Root Cause
Flask 2.3+ removed the deprecated `ENV` config key. The codebase pinned Flask 3.1.3 (latest), but `wsgi.py:67` tried to access the non-existent key, causing all gunicorn workers to fail at import time.

**Impact**: 
- Both Flask workers exited with code 3 (import failure)
- Gunicorn master detected worker failure and shut down
- Entire application failed to start
- No logs reached the app console (pipe redirection issue in launcher)

---

## Solution: Four-Phase Fix

### Phase 1: Hotfix (Critical)
**File**: `wsgi.py`

- **Remove** deprecated `app.config['ENV']` access
- **Add** env normalization: fall back to `production` if `FLASK_ENV` is invalid (e.g., `prod`, `Production`)
- **Log** `flask_env` + `app.debug` instead

**Result**: App boots successfully; no more KeyError.

---

### Phase 2: Startup-Path Correctness

#### 2a. Remove module-level SIGTERM handler in wsgi.py
**Problem**: gunicorn has a built-in graceful-drain mechanism triggered by SIGTERM. Workers at line 95 overwrote it with a bare `sys.exit(0)`, breaking graceful shutdown.

**Solution**: Remove the signal handler from wsgi.py. The launcher (`run_app.py:96`) already handles SIGTERM correctly at the process level.

#### 2b. Fix FastAPI logging in run_app.py
**Problem**: `subprocess.Popen(..., stdout=PIPE, stderr=STDOUT)` with no drain → pipe fills (~64KB), uvicorn blocks, logs lost.

**Solution**: Remove `stdout`/`stderr` kwargs; let uvicorn inherit and stream logs directly to Databricks Apps console.

#### 2c. Exit with child's return code
**Problem**: Launcher always exited with code 0, masking child crashes.

**Solution**: `sys.exit(exit_code or 1)` when either child dies → Databricks sees proper exit codes.

#### 2d. Delete stale web_app/app.yaml
**Problem**: Duplicate manifest with hardcoded `SECRET_KEY: "changeme-in-production-use-secrets"` and wrong port binding (ignores `DATABRICKS_APP_PORT` env var).

**Solution**: Remove it; root `app.yaml` is authoritative.

---

### Phase 3: Silent-Failure Cleanup

#### 3a. Rename shared_library/global_logger → shared_library/global_logger_hub
**Problem**: 
- All imports reference `global_logger_hub` (wsgi.py, start_server.py, and the package's own internals)
- Directory was named `global_logger`, causing silent ImportError in `except` blocks
- MLflow tracing and global logging were dead code in production

**Solution**: 
- Rename directory to match all imports
- Add `shared_library/__init__.py` to make it a proper package

#### 3b. Improve MLflow default URI
**Problem**: Default was `http://127.0.0.1:5000` (no listener in container); blocked on retry attempts.

**Solution**: 
- Use `databricks` URI when `DATABRICKS_HOST` is set (production)
- Make tracing opt-in; skip if neither is configured
- Non-blocking: log and continue

#### 3c. Clarify SECRET_KEY handling
**Problem**: ProductionConfig would raise RuntimeError at import time even if using DevelopmentConfig.

**Solution**: 
- Allow `SECRET_KEY=None` at class level (deferred validation)
- Flask will fail at first session write if missing (not at boot)
- Document: set via app.yaml secret binding

#### 3d. Fix multi-worker seed race
**Problem**: With `gunicorn -w 2`, both workers called `seed_database()` simultaneously, causing race conditions.

**Solution**: File lock (`/tmp/procure_ai_seed.lock`) ensures only first worker seeds; second skips.

#### 3e. Declare flask-cors explicitly
**Problem**: Imported directly but not declared; resolves only transitively via mlflow (silent breakage risk).

**Solution**: Add `flask-cors>=6.0.5` to `pyproject.toml` + regenerate `requirements.txt`.

---

### Phase 4: Prevent Recurrence

**File**: `ops/tests/test_startup.py`

Comprehensive smoke test suite covering:
- ✅ WSGI import in production + development configs
- ✅ Environment normalization and fallback
- ✅ Flask app factory
- ✅ Invalid FLASK_ENV handling
- ✅ Blueprint registration

**Pre-deployment gate**:
```bash
FLASK_ENV=development uv run pytest ops/tests/test_startup.py -v
# All tests must pass
```

Or for production validation:
```bash
FLASK_ENV=production SECRET_KEY=test python -c "import sys; sys.path.insert(0, '.'); import wsgi; print('PASS')"
```

---

## Verification

### Test Results
```
ops/tests/test_startup.py::test_wsgi_import_production PASSED
ops/tests/test_startup.py::test_wsgi_import_development PASSED
ops/tests/test_startup.py::test_flask_app_factory_production PASSED
ops/tests/test_startup.py::test_flask_app_factory_development PASSED
ops/tests/test_startup.py::test_invalid_flask_env_defaults_to_production PASSED
ops/tests/test_startup.py::test_production_config_with_missing_secret_key PASSED
ops/tests/test_startup.py::test_app_has_required_blueprints PASSED

======================== 7 passed ========================
```

### Rollout Checklist
- [x] All critical startup errors fixed
- [x] Module imports work in all configs
- [x] Flask app factory tests pass
- [x] Environment normalization tested
- [x] Smoke test suite created
- [x] Code committed with conventional messages
- [x] No backward compatibility breaks

---

## Files Changed

| File | Change | Reason |
|------|--------|--------|
| `wsgi.py` | Fix KeyError, add env normalization, remove SIGTERM | Phase 1 + 2 |
| `web_app/config.py` | Clarify SECRET_KEY handling | Phase 3 |
| `web_app/seed.py` | Add file lock for multi-worker safety | Phase 3 |
| `web_app/__init__.py` | (no change) | Documented in commit |
| `ops/deployment/run_app.py` | Fix FastAPI logging, exit codes | Phase 2 |
| `web_app/app.yaml` | (deleted) | Phase 2 |
| `pyproject.toml` | Add flask-cors explicit dep | Phase 3 |
| `requirements.txt` | Regenerated | Phase 3 |
| `shared_library/global_logger/` → `shared_library/global_logger_hub/` | (renamed) | Phase 3 |
| `shared_library/__init__.py` | (created) | Phase 3 |
| `ops/tests/test_startup.py` | (created) | Phase 4 |

---

## Commits

1. **fix(startup): resolve critical Flask app initialization errors**
   - 24 files changed: phases 1-3, 11 fixes
   
2. **test(startup): fix smoke test suite**
   - Test suite validated and passing

---

## Post-Deployment Tasks

✅ **Done**:
- All fixes committed
- Tests passing locally
- Ready to redeploy to Databricks Apps

**Next Agent**:
1. Deploy `main` branch to Databricks App `ai-saas`
2. Monitor logs for successful startup
3. Verify X-Forwarded headers are present in first login request
4. Update Sprint 1 dashboard with deployment status

---

## Learnings

1. **Deprecated APIs**: Flask 2.3+ removes `ENV` key. Always check Flask changelog before upgrading.
2. **Silent Failures**: Import errors in `except` blocks are invisible. Use explicit logging or tests.
3. **Multi-Worker Initialization**: Gunicorn workers run independently; races on file state require coordination (file locks, env flags).
4. **Process Supervision**: Exit codes matter. Always propagate child crashes to launcher → orchestration layer.
5. **Pre-Deploy Smoke Tests**: A simple 1-line import test (`FLASK_ENV=production SECRET_KEY=test python -c "import wsgi"`) would have caught this locally.

---

## Questions for Next Agent

- Should we add the smoke test to the CI/CD pipeline (`.github/workflows/` or Databricks DAB pre-deploy hook)?
- Should we document the `SEED_ON_STARTUP` env flag for future use (currently always enabled via lock)?
- Is there an actual MLflow tracking server the app should connect to in production, or is it opt-in for now?
