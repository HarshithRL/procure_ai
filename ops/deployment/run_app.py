#!/usr/bin/env python3
"""Dual-process launcher for Procure AI.

Spawns two subprocesses:
1. FastAPI agent_server on port 8001 (uvicorn)
2. Flask web_app on port $DATABRICKS_APP_PORT (gunicorn)

Coordinates graceful shutdown on SIGTERM (15-second window).
"""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
import time


def main():
    """Start both Flask and FastAPI servers."""
    # Determine Flask app port (Databricks Apps injects DATABRICKS_APP_PORT)
    flask_port = os.getenv("DATABRICKS_APP_PORT", "8000")
    flask_workers = os.getenv("GUNICORN_WORKERS", "2")

    print("[launcher] Starting Procure AI dual-process server...")
    print(f"[launcher] Flask will bind to 0.0.0.0:{flask_port} (workers={flask_workers})")
    print("[launcher] FastAPI will bind to 0.0.0.0:8001")

    # Start FastAPI server (uvicorn)
    fastapi_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "agent_server.start_server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8001",
            "--loop",
            "auto",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Give FastAPI time to start
    time.sleep(2)

    # Start Flask server (gunicorn)
    # Use wsgi:app — wsgi.py is at project root with module-level app object
    flask_proc = subprocess.Popen(
        [
            "gunicorn",
            "wsgi:app",
            "-w",
            flask_workers,
            "-b",
            f"0.0.0.0:{flask_port}",
            "--timeout",
            "60",
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
        ],
    )

    print("[launcher] Both servers started. Press Ctrl+C to stop.")

    def handle_sigterm(signum, frame):
        """Handle SIGTERM signal — graceful shutdown."""
        print("\n[launcher] SIGTERM received. Initiating graceful shutdown...")
        print("[launcher] Terminating FastAPI...")
        fastapi_proc.terminate()
        try:
            fastapi_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("[launcher] FastAPI did not stop gracefully; killing...")
            fastapi_proc.kill()

        print("[launcher] Terminating Flask...")
        flask_proc.terminate()
        try:
            flask_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("[launcher] Flask did not stop gracefully; killing...")
            flask_proc.kill()

        print("[launcher] Shutdown complete.")
        sys.exit(0)

    # Register signal handler
    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        # Wait for both processes
        while fastapi_proc.poll() is None and flask_proc.poll() is None:
            time.sleep(1)

        # If one exits, stop the other
        if fastapi_proc.poll() is not None:
            print(f"[launcher] FastAPI exited with code {fastapi_proc.returncode}")
            flask_proc.terminate()
            flask_proc.wait()

        if flask_proc.poll() is not None:
            print(f"[launcher] Flask exited with code {flask_proc.returncode}")
            fastapi_proc.terminate()
            fastapi_proc.wait()

    except KeyboardInterrupt:
        print("\n[launcher] Interrupted. Shutting down...")
        fastapi_proc.terminate()
        flask_proc.terminate()
        try:
            fastapi_proc.wait(timeout=5)
            flask_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            fastapi_proc.kill()
            flask_proc.kill()
        sys.exit(0)


if __name__ == "__main__":
    main()
