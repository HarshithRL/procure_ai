#!/usr/bin/env python3
"""Dual-process launcher for Procure AI.

Spawns two subprocesses:
1. FastAPI agent_server on port 8001 (uvicorn)
2. Flask web_app on port $DATABRICKS_APP_PORT

Web server selection is platform-aware:
- POSIX (Databricks Apps, Docker, Linux/macOS dev): gunicorn
- Windows: gunicorn cannot run (it imports `fcntl`, which does not exist on
  Windows), so we fall back to waitress, and then to the werkzeug dev server.

Coordinates graceful shutdown on SIGTERM (15-second window).
"""

from __future__ import annotations

import importlib.util
import os
import signal
import subprocess
import sys
import time

IS_WINDOWS = os.name == "nt"


def _module_available(name: str) -> bool:
    """Return True if `name` can be imported without actually importing it."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def build_flask_command(flask_port: str, flask_workers: str) -> tuple[list[str], str]:
    """Choose the WSGI server command for the current platform.

    Returns:
        (argv, human_readable_server_name)
    """
    if not IS_WINDOWS:
        return (
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
            f"gunicorn (workers={flask_workers})",
        )

    # Windows: gunicorn is not importable (no fcntl).
    if _module_available("waitress"):
        return (
            [
                sys.executable,
                "-m",
                "waitress",
                f"--listen=0.0.0.0:{flask_port}",
                "--threads=8",
                "wsgi:app",
            ],
            "waitress (threads=8)",
        )

    # Last resort: werkzeug dev server via wsgi.py's __main__ block.
    # It reads the port from DATABRICKS_APP_PORT, which main() exports below.
    # Not production grade, but keeps local development unblocked.
    return ([sys.executable, "wsgi.py"], "werkzeug dev server (waitress not installed)")


def main():
    """Start both Flask and FastAPI servers."""
    # Determine Flask app port (Databricks Apps injects DATABRICKS_APP_PORT)
    flask_port = os.getenv("DATABRICKS_APP_PORT", "8000")
    flask_workers = os.getenv("GUNICORN_WORKERS", "2")

    flask_cmd, flask_server_name = build_flask_command(flask_port, flask_workers)

    # Ensure the werkzeug fallback (and any child) sees the resolved port.
    os.environ["DATABRICKS_APP_PORT"] = flask_port

    print("[launcher] Starting Procure AI dual-process server...")
    print(f"[launcher] Platform: {'Windows' if IS_WINDOWS else 'POSIX'}")
    print(f"[launcher] Flask will bind to 0.0.0.0:{flask_port} via {flask_server_name}")
    print("[launcher] FastAPI will bind to 0.0.0.0:8001")

    # Start FastAPI server (uvicorn)
    # Note: Do NOT redirect stdout/stderr; allow uvicorn to inherit and stream logs to Databricks Apps console.
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
    )

    # Give FastAPI time to start
    time.sleep(2)

    # Start Flask server (platform-appropriate WSGI server, see build_flask_command)
    # Use wsgi:app — wsgi.py is at project root with module-level app object
    flask_proc = subprocess.Popen(flask_cmd)

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

        # If one exits, stop the other and propagate its exit code
        if fastapi_proc.poll() is not None:
            exit_code = fastapi_proc.returncode
            print(f"[launcher] FastAPI exited with code {exit_code}")
            flask_proc.terminate()
            flask_proc.wait()
            sys.exit(exit_code or 1)

        if flask_proc.poll() is not None:
            exit_code = flask_proc.returncode
            print(f"[launcher] Flask exited with code {exit_code}")
            fastapi_proc.terminate()
            fastapi_proc.wait()
            sys.exit(exit_code or 1)

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
