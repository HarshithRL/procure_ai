"""
Database seeding module.

DEPRECATED: No seed data. Users are auto-provisioned from Databricks SSO headers
(X-Forwarded-Email, X-Forwarded-User, X-Forwarded-Preferred-Username) on first login.
Projects are created via the UI by authenticated users, not seeded at startup.

This function is retained for database cleanup and maintenance.
"""

import os
from .models import Project, User


def seed_database(session) -> None:
    """
    Initialize database: clear stale seed data and maintain clean state.

    BEHAVIOR:
    - Detects if old seeded projects exist (from pre-SSO bootstrap)
    - Deletes all projects owned by the hardcoded seed email
    - Deletes the hardcoded seed user if present
    - All users are auto-provisioned from SSO headers on first login
    - All projects created via UI by authenticated users (owner_email tenant-scoped)

    This aligns with the Databricks Apps SSO architecture (auth.md).
    """
    # The old hardcoded seed email that should be removed
    OLD_SEED_EMAIL = "harshith.raghunath@etexgroup.com"
    
    # Delete all projects owned by the old seed user (cleanup)
    session.query(Project).filter(Project.owner_email == OLD_SEED_EMAIL).delete()
    session.commit()
    
    # Delete the old seed user if it exists (no bootstrap users anymore)
    session.query(User).filter(User.email == OLD_SEED_EMAIL).delete()
    session.commit()
    
    # Log the cleanup
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Database initialized: removed stale seed data (email=%s)", OLD_SEED_EMAIL)
