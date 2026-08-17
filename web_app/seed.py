"""
Database seeding module.

DEPRECATED: No seed data. Users are auto-provisioned from Databricks SSO headers
(X-Forwarded-Email, X-Forwarded-User, X-Forwarded-Preferred-Username) on first login.
Projects are created via the UI by authenticated users, not seeded at startup.

This function is retained as a no-op for backward compatibility with create_app().
Future: Can be removed entirely if caller is refactored.
"""


def seed_database(session) -> None:
    """
    Seed the database with initial data.

    CURRENT BEHAVIOR: No-op. All data is created on-demand:
    - Users: Auto-provisioned from SSO headers on first request
    - Projects: Created via UI by authenticated users (owner_email tenant-scoped)

    This aligns with the Databricks Apps SSO architecture (auth.md) where users
    must be resolved from X-Forwarded-* headers, never hardcoded in code.
    """
    return
