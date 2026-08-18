"""Model Factory error types."""

from __future__ import annotations


class ModelFactoryError(Exception):
    """Base error for the Model Factory package."""


class RegistryError(ModelFactoryError):
    """Raised when a registry file is missing, malformed, or incomplete."""


class AuthBridgeError(ModelFactoryError):
    """Raised when Databricks credentials cannot be resolved for AI Gateway."""


class ResolveError(ModelFactoryError):
    """Raised when a profile/model cannot be resolved to a chat model."""
