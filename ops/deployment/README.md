# Procure AI Deployment Guide

## Architecture

Procure AI uses a **dual-process architecture**:

1. **FastAPI Agent Server** (port 8001) — LangGraph agent orchestration + SSE streaming
   - Handles `/api/v1/agents/stream` (SSE), `/api/v1/agents/invoke` (sync), health checks
   - Entry point: `uvicorn agent_server.start_server:app --host 0.0.0.0 --port 8001`

2. **Flask Web App** (port 5000/8000) — Web UI + BFF proxy
   - Renders Jinja2 templates, serves static assets
   - Routes `/bff/*` requests to FastAPI agent server
   - Health check at `/bff/health` proxies to FastAPI `/health`
   - Entry point: `gunicorn wsgi:app` or `flask --app wsgi run`

The **BFF (Backend-for-Frontend) proxy** in Flask (`web_app/blueprints/bff.py`) ensures:
- X-Forwarded-* headers from Databricks Apps SSO are passed through
- Chat UI can communicate with agent_server via same origin (Flask)
- Agent status polls `/bff/health`, which proxies to FastAPI

---

## Deployment Scenarios

### Scenario 1: Local Development (Dual-Server with Hot Reload)

Start both servers together with automatic reloading:

```bash
uv run python ops/deployment/run_app.py
```

Then open: http://127.0.0.1:5000/chat

**Expected behavior:**
- FastAPI starts on port 8001 (reload enabled)
- Flask starts on port 5000 (werkzeug dev server with hot reload)
- Agent status pill shows "● Agent connected" after 3-5 seconds
- Message sending works end-to-end

---

### Scenario 2: Local Development (Flask Only)

If you only want to develop the Flask UI without agent interaction:

```bash
# Option A: Flask CLI (recommended)
uv run flask --app wsgi run --debug --port 5000

# Option B: Direct Python
python wsgi.py
```

**Expected behavior:**
- Flask starts on port 5000
- Chat UI loads
- Agent status shows "● Agent checking..." (offline)
- Message sending will fail with "agent_server unreachable"

To fix: Start FastAPI separately in another terminal:
```bash
uv run uvicorn agent_server.start_server:app --reload --port 8001
```

---

### Scenario 3: Production (Databricks Apps)

The app `ai-saas` is configured to run `ops/deployment/run_app.py`:

```yaml
# app.yaml (Databricks Apps config)
source_code_path: /Workspace/Users/.../procure-ai
command: ["python", "ops/deployment/run_app.py"]
```

Then Databricks Apps:
1. Injects `DATABRICKS_APP_PORT` (typically 8000)
2. Routes incoming traffic to port 8000 (Flask)
3. Flask proxies agent requests to FastAPI on 8001 (localhost)

**Port binding:**
- FastAPI binds to 0.0.0.0:8001 (internal only)
- Flask binds to 0.0.0.0:$DATABRICKS_APP_PORT (exposed via Databricks proxy)

---

### Scenario 4: Production (Docker / Kubernetes)

Deploy as two separate containers:

**Container 1 (Agent)**
```dockerfile
CMD ["uvicorn", "agent_server.start_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Container 2 (Web)**
```dockerfile
CMD ["gunicorn", "wsgi:app", "-w", "4", "-b", "0.0.0.0:8000"]
ENV AGENT_SERVER_URL="http://agent-service:8001"  # Host discovery
```

Override `AGENT_SERVER_URL` in Flask config if needed (see `web_app/blueprints/bff.py:21`).

---

## Debugging: Agent Shows "Offline"

If the chat UI's agent status pill shows "● Agent checking..." instead of "● Agent connected":

### Step 1: Check if FastAPI is running

```bash
curl http://127.0.0.1:8001/health
```

**Expected response:**
```json
{
  "status": "ok",
  "graph_ready": true,
  "service": "Procure AI Agent API"
}
```

**If connection refused:** Start FastAPI:
```bash
uv run uvicorn agent_server.start_server:app --reload --port 8001
```

### Step 2: Check Flask's proxy

```bash
curl http://127.0.0.1:5000/bff/health
```

**Expected response:**
```json
{
  "status": "ok",
  "graph_ready": true,
  "service": "Procure AI Agent API"
}
```

**If error response:** Check Flask logs for proxy issues:
- Look for `[BFF] health error` messages
- Verify `AGENT_SERVER_URL` in `web_app/blueprints/bff.py:21` is correct
- Ensure FastAPI is listening on the specified port/host

### Step 3: Check browser console

Open http://127.0.0.1:5000/chat and inspect browser DevTools:
- Network tab: `/bff/health` requests should return 200
- Console: Check for JavaScript errors in `chat-stream.js`
- Verify `fetch('/bff/health')` succeeds

### Step 4: View Flask logs

If running locally, Flask logs should show:
```
[BFF] checking agent health at http://127.0.0.1:8001/health
[BFF] agent health ok | graph_ready=true
```

If you see:
```
[BFF] cannot connect to agent_server | error=ConnectionRefusedError
```

Then FastAPI is not running. Start it as shown in Step 1.

---

## Environment Variables

### Development

No variables needed; defaults work fine.

### Production (Databricks Apps)

Set these in `app.yaml` or Databricks Secrets:

```yaml
env:
  FLASK_ENV: "production"
  DATABRICKS_APP_PORT: "8000"
  SECRET_KEY: "{{ secret:/procure-ai-secrets/flask-secret-key }}"
  # Optional:
  DATABASE_URL: "postgresql://user:pass@lakebase-host/procure_ai"
  MLFLOW_TRACKING_URI: "https://adb-xxx.azuredatabricks.net/api/2.0/mlflow-tracking"
  MLFLOW_EXPERIMENT: "/procure_ai"
```

### Agent Server Config

Edit `agent_server/core/config.py` to customize:
- LLM model selection
- Vector store endpoints
- Tool definitions
- Tracing/logging

---

## Health Check & Readiness

### Liveness Probe

```bash
curl http://127.0.0.1:5000/  # Flask root
curl http://127.0.0.1:8001/  # FastAPI root
```

### Readiness Probe

```bash
# Agent server ready for requests?
curl http://127.0.0.1:8001/health

# Flask proxy working?
curl http://127.0.0.1:5000/bff/health
```

Both should return HTTP 200 with JSON.

---

## Graceful Shutdown

Both servers handle SIGTERM (e.g., from Kubernetes/Docker):

- **FastAPI** (uvicorn): Waits for active requests to complete (~5s timeout)
- **Flask** (gunicorn): Workers gracefully finish requests, main process exits

The launcher (`run_app.py`) coordinates shutdown:
1. Receives SIGTERM
2. Sends SIGTERM to both child processes
3. Waits up to 5s for graceful exit
4. Force-kills any stragglers

---

## Performance Tuning

### Flask (Gunicorn)

In production, adjust workers:

```bash
gunicorn wsgi:app \
  -w 4 \             # 2-4 * CPU cores
  -b 0.0.0.0:8000 \
  --timeout 60 \     # Max request time
  --access-logfile - --error-logfile -
```

### FastAPI (Uvicorn)

For high concurrency, use Hypercorn or Uvloop:

```bash
uvicorn agent_server.start_server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 2 \              # For multiple CPUs
  --loop uvloop \            # Faster event loop
  --ws-max-size 16_777_216   # Large WebSocket frames if needed
```

---

## Troubleshooting Checklist

- [ ] Both servers running on correct ports? (`netstat -tlnp` on Linux, `netstat -ano` on Windows)
- [ ] Firewall allows 5000/8001 locally? (`curl 127.0.0.1:5000` and `:8001`)
- [ ] Flask logs show no import errors? (check stdout for tracebacks)
- [ ] Agent logs show graph loaded? (look for "Agent graph warmed up")
- [ ] `/bff/health` returns `"status": "ok"`? (proxies working)
- [ ] Browser console shows no 404s or CORS errors?
- [ ] Cookies set correctly? (check Storage → Cookies in DevTools)

---

## Related Files

- `wsgi.py` — WSGI entry point (canonical)
- `app.py` — Dev convenience entry point
- `run_app.py` — Dual-process launcher
- `web_app/blueprints/bff.py` — BFF proxy logic
- `agent_server/start_server.py` — FastAPI app
- `web_app/static/dist/chat-stream.js` — UI health check polling
