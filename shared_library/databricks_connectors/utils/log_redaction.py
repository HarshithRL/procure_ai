"""Log filters that redact Databricks credentials from log records."""

from __future__ import annotations

import logging
import re
from typing import Iterable, Optional

# Bearer tokens, Databricks PATs (dapi...), and forwarded access-token header values
_SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"\bdapi[a-zA-Z0-9]{20,}\b"),
    re.compile(
        r"(?i)(x-forwarded-access-token\s*[:=]\s*)(\S+)",
    ),
    re.compile(
        r"(?i)((?:access[_-]?token|client_secret|DATABRICKS_TOKEN|DATABRICKS_CLIENT_SECRET)"
        r"\s*[:=]\s*)(\S+)",
    ),
)

_REDACTED = "[REDACTED]"

_INSTALLED = False


class SensitiveDataRedactor(logging.Filter):
    """Strip secrets from log messages without false-positives on 'token_count'."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001
            return True
        redacted = message
        for pattern in _SENSITIVE_PATTERNS:
            if pattern.groups >= 1:
                redacted = pattern.sub(rf"\1{_REDACTED}", redacted)
            else:
                redacted = pattern.sub(_REDACTED, redacted)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def install_databricks_log_redaction(
    logger_names: Optional[Iterable[str]] = None,
) -> SensitiveDataRedactor:
    """Attach redaction filter to Databricks / connector / agent_server loggers."""
    global _INSTALLED
    redactor = SensitiveDataRedactor()
    names = list(
        logger_names
        or (
            "databricks.sdk",
            "databricks",
            "databricks_connectors",
            "databricks_connectors.auth",
            "databricks_connectors.hub",
            "databricks_connectors.identity",
            "databricks_connectors.fastapi_deps",
            "agent_server",
            "agent_server.start_server",
            "agent_server.auth",
            "agent_server.api.router",
        )
    )
    for name in names:
        target = logging.getLogger(name)
        # Avoid duplicate filters on re-import / reload
        if not any(isinstance(f, SensitiveDataRedactor) for f in target.filters):
            target.addFilter(redactor)
    _INSTALLED = True
    return redactor


def redact_secrets(text: str) -> str:
    """Redact secrets in an arbitrary string (for tests / ad-hoc scrubbing)."""
    out = text
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.groups >= 1:
            out = pattern.sub(rf"\1{_REDACTED}", out)
        else:
            out = pattern.sub(_REDACTED, out)
    return out
