# Procure AI Startup Failure — Debug Report

**Issue Date**: 2026-08-18 05:27:52 UTC  
**Diagnosis Complete**: 2026-08-18 11:15 UTC  
**Status**: ✅ **RESOLVED**

---

## Original Error

```
[2026-08-18 05:27:52 +0000] [702] [ERROR] Exception in worker process
Traceback (most recent call last):
  File "/app/python/source_code/wsgi.py", line 67, in <module>
    logger.info(f"Flask app created | env={flask_env} | config={app.config['ENV']}")
                                                                ~~~~~~~~~~^^^^^^^
KeyError: 'ENV'
```

**Symptom**: Both gunicorn workers failed to boot → Gunicorn master shut down → app unreachable

---

## Root Cause Analysis

### Why `app.config['ENV']` failed

Flask 2.3.0 (released Sept 2023) deprecated and removed the `ENV` config key:
- Old: `app.config['ENV']` → `'development'` or `'production'`
- New: `app.debug` → `True` or `False`
- Migration guide: Flask 2.3.0 release notes (Sep 2023)

**Codebase Status**:
- `pyproject.toml`: pins `flask>=3.0.0` (latest, released Dec 2023)
- `uv.lock`: resolved to `flask==3.1.3`
- `wsgi.py:67`: accessed `app.config['ENV']` (removed 7 months prior)
- **Result**: Guaranteed crash on any import of wsgi.py

### Why It Reached Production

**No pre-deployment smoke test** — The production import path was never validated:
```bash
# This would have caught it locally in seconds:
FLASK_ENV=production SECRET_KEY=test python -c "import wsgi"
# KeyError: 'ENV' ← CAUGHT
```

---

## Cascade Failures

| Layer | Failure | Impact |
|-------|---------|--------|
| **wsgi.py:67** | KeyError: 'ENV' | Module import fails |
| **gunicorn worker** | `load_wsgi()` crashes | Worker exit code 3 |
| **gunicorn arbiter** | Worker failed to boot | Master stops accepting requests |
| **run_app.py:100-112** | Child exits code 3 | Main process sees exit, doesn't propagate it |
| **Databricks Apps** | Exit code 0 (normal exit) | Doesn't know there was a crash |
| **Logs** | FastAPI pipe redirection | Buffer filled → uvicorn blocked → no logs |
| **Silent failures** | MLflow import error swallowed | Dead code in except block |

**Lesson**: One-line bug cascaded through 5 layers due to insufficient error visibility.

---

## All Issues Found

### Critical (Production Impact)
| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | wsgi.py | 67 | Access deprecated `app.config['ENV']` | ✅ Log `app.debug` instead |
| 2 | run_app.py | 45-46 | FastAPI logs lost (pipe redirect) | ✅ Remove stdout/stderr pipes |
| 3 | run_app.py | 100-112 | Child crash → exit 0 (masking error) | ✅ `sys.exit(exit_code or 1)` |
| 4 | wsgi.py | 95 | Module-level SIGTERM overwrites gunicorn's | ✅ Remove, defer to launcher |

### High (Silent Failures)
| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 5 | shared_library/global_logger/ | - | Package imported as `global_logger_hub` but named `global_logger` | ✅ Rename directory |
| 6 | wsgi.py | 48 | MLflow default `http://127.0.0.1:5000` → no listener | ✅ Use `databricks` when on Databricks |
| 7 | web_app/__init__.py | 19 | Multi-worker seed race on `/tmp/procure_ai.db` | ✅ Add file lock |
| 8 | web_app/app.yaml | - | Stale duplicate manifest with hardcoded SECRET_KEY | ✅ Delete |

### Medium (Data Quality / Configuration)
| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 9 | wsgi.py | 64-67 | Invalid FLASK_ENV (e.g., 'prod') → KeyError | ✅ Normalize + fall back to production |
| 10 | pyproject.toml | - | flask-cors imported but not declared (transitive via mlflow) | ✅ Declare explicitly |
| 11 | web_app/config.py | 26 | Missing SECRET_KEY not validated at boot | ✅ Deferred validation (doc) |

---

## Fixes Applied

### Commit 1: fix(startup)
- ✅ Remove deprecated `app.config['ENV']`
- ✅ Add FLASK_ENV normalization
- ✅ Remove module-level SIGTERM handler
- ✅ Fix FastAPI logging pipes
- ✅ Exit with child return code
- ✅ Delete web_app/app.yaml
- ✅ Rename global_logger → global_logger_hub
- ✅ Improve MLflow URI default
- ✅ Fix seed race with file lock
- ✅ Declare flask-cors explicitly

**Files**: 24 changed, ~900 insertions

### Commit 2: test(startup)
- ✅ Create comprehensive smoke test suite
- ✅ Test production + development configs
- ✅ Test env normalization
- ✅ Test blueprint registration

**Files**: 1 new file, 150 lines, 7 tests (all passing)

### Commit 3: docs(handoff)
- ✅ Document fix summary and learnings
- ✅ Guide next agent on deployment

---

## Verification

### Local Testing (Windows)
```powershell
# Production config
PS> $env:FLASK_ENV="production"; $env:SECRET_KEY="test"; $env:DATABASE_URL="sqlite:///:memory:"
PS> python -c "import sys; sys.path.insert(0, '.'); import wsgi; print('✓ SUCCESS')"
✓ SUCCESS

# Development config
PS> $env:FLASK_ENV="development"
PS> python -c "import sys; sys.path.insert(0, '.'); import wsgi; print('✓ SUCCESS')"
✓ SUCCESS
```

### Test Suite
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

---

## What Changed for the User

**Before**:
```
[2026-08-18 05:27:52] [702] [ERROR] Exception in worker process
KeyError: 'ENV'
Worker failed to boot.
```
→ **App crashes, completely unavailable**

**After**:
```
2026-08-18 11:11:06 | INFO | pdf_engine | logging.configured
2026-08-18 11:11:11 - wsgi - INFO - MLflow tracing bootstrapped | uri=databricks | exp=procure_ai
2026-08-18 11:11:11 - wsgi - INFO - Flask app created | env=production | debug=False
```
→ **App boots successfully**

---

## Deployment Readiness

✅ **All critical issues fixed**  
✅ **Tests passing**  
✅ **Smoke test suite created (pre-deploy gate)**  
✅ **No backward compatibility breaks**  
✅ **Commits follow conventional style**  
✅ **Handoff documentation complete**

**Next Steps** (for deployment agent):
1. `git push origin main`
2. `databricks apps deploy ai-saas --source-code-path .`
3. Monitor logs for successful startup
4. Verify X-Forwarded headers on first login
5. Update Sprint 1 delivery status

---

## Prevention

To prevent similar issues:

1. **Add pre-deployment smoke test to CI/CD**:
   ```bash
   FLASK_ENV=production SECRET_KEY=test python -c "import wsgi"
   ```

2. **Enforce dependency updates**:
   - Pin major versions (e.g., `flask>=3.0,<4.0`)
   - Review changelogs for breaking changes

3. **Test production import path**:
   - Never assume dev-only imports work in prod
   - Always test the actual entry point: `gunicorn wsgi:app`

4. **Visible error handling**:
   - Avoid broad `except ImportError` without logging
   - Use explicit exception types

5. **Process supervision**:
   - Exit codes matter: propagate child crashes
   - Log subprocess output in real-time (no pipe buffering)

---

# Part 2 — Deployment Round (same day)

Fixing the startup crash unblocked the app, but deploying it surfaced four more
defects. Three were pre-existing and previously **invisible**, because FastAPI's
stdout was being swallowed by the unread subprocess pipe (Part 1, issue #2).
Fixing log visibility is what made them observable.

| # | Stage | Error | Cause | Fix |
|---|-------|-------|-------|-----|
| 12 | BUILD | `No matching distribution found for pywin32==312` | **Self-inflicted.** `uv pip compile` was run on Windows and committed, pinning Windows-only wheels (`pywin32` via mlflow→docker, `win32-setctime` via loguru) with no platform markers. Databricks Apps builds on Ubuntu 22.04. | Restored the hand-maintained 54-line loose `requirements.txt`; added only `flask-cors`; added a header warning + `--python-platform linux` escape hatch |
| 13 | RUNTIME | `INVALID_PARAMETER_VALUE: Got an invalid experiment name 'procure_ai'` | Databricks-managed MLflow requires **absolute workspace paths**. Both entry points used bare names. | Default to `/Shared/procure_ai`; normalize non-absolute names; declare `MLFLOW_TRACKING_URI`/`MLFLOW_EXPERIMENT` in `app.yaml` |
| 14 | RUNTIME | `Graph warm-up error: Prompt not found: .../brain/SYSTEM_PROMPT.md` | `databricks.yml` excluded `"*.md"` from sync — which also stripped the agent's **runtime prompt assets**. The agent was starting with no system prompt. | Removed the blanket glob (root docs were already listed individually); documented why it must not return |
| 15 | BUILD | `error resolving resource secret/procure-ai/secret-key for env SECRET_KEY` | `valueFrom` resolves an **app resource key**, not a secret path. The secret existed but was never attached to the app, so `SECRET_KEY` was never injected → `ProductionConfig.SECRET_KEY = None` → Flask sessions would 500 on first write. | Attached the secret as app resource `secret-key` (READ); `valueFrom: secret-key` |

### Deployment commands used

```powershell
# Attach the secret as an app resource (one-time)
databricks apps update ds-procure-ai --profile adb-7181820732839861 --json '{
  "resources": [{
    "name": "secret-key",
    "secret": {"scope": "procure-ai", "key": "secret-key", "permission": "READ"}
  }]
}'

# Deploy
databricks bundle deploy -t dev --profile adb-7181820732839861
databricks apps deploy ds-procure-ai `
  --source-code-path /Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent/files `
  --profile adb-7181820732839861
```

> **Note on `deploy.ps1`**: piping it through `2>&1` in PowerShell trips
> `$ErrorActionPreference = "Stop"`, because the Databricks CLI writes progress to
> stderr and PowerShell surfaces that as a `NativeCommandError`. Run the script
> without redirection, or invoke the CLI steps directly.

### Final verified state

```
URL          : https://ds-procure-ai-7181820732839861.1.azure.databricksapps.com
App state    : RUNNING - App is running
Compute      : ACTIVE
Deploy state : SUCCEEDED
Resources    : secret-key
```

```
[launcher] Starting Procure AI dual-process server...
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Booting worker with pid: 990
[INFO] Booting worker with pid: 991
INFO:     Started server process [987]
MLflow bootstrapped | uri=databricks | exp=/Shared/procure_ai
Brain agent compiled | tools=0 | model_type=ConstraintAwareChatModel
Graph built | id=procure_orchestrator
Agent graph warmed up          <-- previously failed silently
Server startup complete
```

No errors, no tracebacks, no unresolved resources.

### Additional learnings

6. **Never commit a lockfile compiled on a different OS than the deploy target.**
   `uv pip compile` bakes in platform-specific transitive deps with no markers.
   Use `--python-platform linux`, or keep the file loose and let the Linux build
   host resolve.
7. **Blanket file-exclusion globs are dangerous when code loads data files.**
   `"*.md"` looked like a docs filter; it was actually stripping agent prompts.
   Exclude directories and named files, not extensions.
8. **`valueFrom` is a resource-key indirection, not a path.** A secret existing in
   a scope is necessary but not sufficient — it must be attached to the app.
9. **Fixing observability pays compound interest.** Issues #13, #14 and #15 were
   all already present; they only became diagnosable after the stdout pipe fix.

---

## Questions?

See `.design_docs/assistent/handoffs/STARTUP_FIX_SUMMARY.md` for detailed solution guide.
