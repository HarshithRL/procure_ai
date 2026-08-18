"""
Database seeding module.

DEPRECATED: No seed data. Users are auto-provisioned from Databricks SSO headers
(X-Forwarded-Email, X-Forwarded-User, X-Forwarded-Preferred-Username) on first login.
Projects are created via the UI by authenticated users, not seeded at startup.

This function is retained for database cleanup and maintenance.

MULTI-WORKER SAFETY: Uses a file lock to ensure only one gunicorn worker performs initialization.
"""

import logging
import os
import tempfile
from pathlib import Path

from .models import Project, User

logger = logging.getLogger(__name__)

# Seedable only once per process — file lock to coordinate across gunicorn workers
_SEED_LOCK_FILE = Path(tempfile.gettempdir()) / "procure_ai_seed.lock"
_SEED_COMPLETED = False


def seed_database(session) -> None:
    """
    Initialize database: clear stale seed data and maintain clean state.

    BEHAVIOR:
    - Only runs once, guarded by a file lock (multi-worker safe)
    - Detects if old seeded projects exist (from pre-SSO bootstrap)
    - Deletes all projects owned by the hardcoded seed email
    - Deletes the hardcoded seed user if present
    - All users are auto-provisioned from SSO headers on first login
    - All projects created via UI by authenticated users (owner_email tenant-scoped)

    This aligns with the Databricks Apps SSO architecture (auth.md).
    """
    global _SEED_COMPLETED
    
    if _SEED_COMPLETED:
        return
    
    # Attempt to acquire lock (non-blocking)
    try:
        # Open lock file in exclusive mode (only one writer at a time)
        with open(_SEED_LOCK_FILE, "x"):
            # We have the lock; proceed with seed
            pass
    except FileExistsError:
        # Another worker already ran seed or is running it now
        logger.info("Database seed already in progress or completed; skipping")
        _SEED_COMPLETED = True
        return
    
    try:
        # The old hardcoded seed email that should be removed
        OLD_SEED_EMAIL = "harshith.raghunath@etexgroup.com"
        
        # Delete all projects owned by the old seed user (cleanup)
        session.query(Project).filter(Project.owner_email == OLD_SEED_EMAIL).delete()
        session.commit()
        
        # Delete the old seed user if it exists (no bootstrap users anymore)
        session.query(User).filter(User.email == OLD_SEED_EMAIL).delete()
        session.commit()
        
        logger.info("Database initialized: removed stale seed data (email=%s)", OLD_SEED_EMAIL)
        _SEED_COMPLETED = True
    finally:
        # Clean up lock file
        try:
            _SEED_LOCK_FILE.unlink()
        except Exception:
            pass
