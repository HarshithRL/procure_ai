"""Model Factory — centralized resolver for Databricks Unity AI Gateway.

Public API::

    from shared_library.model_factory import invoke_model, resolve_chat_model

    text = invoke_model("Say hello.", profile="fast_chat")
    llm = resolve_chat_model(profile="deep_reasoning")
"""

from __future__ import annotations

from shared_library.model_factory.auth_bridge import (
    GatewayCredentials,
    resolve_gateway_credentials,
)
from shared_library.model_factory.catalog import (
    get_model_catalog,
    list_models,
    list_profiles,
    peek_resolved_model_key,
    peek_resolved_model_label,
)
from shared_library.model_factory.family_adapter import (
    FamilyPolicy,
    adapt_messages_for_family,
    build_request_params,
    flatten_content_to_text,
    resolve_family_policy,
)
from shared_library.model_factory.exceptions import (
    AuthBridgeError,
    ModelFactoryError,
    RegistryError,
    ResolveError,
)
from shared_library.model_factory.chat_model_wrapper import (
    ConstraintAwareChatModel,
    wrap_with_message_constraints,
)
from shared_library.model_factory.invoke import invoke_model
from shared_library.model_factory.message_constraints import (
    MessageConstraints,
    adapt_messages_for_invoke,
    get_message_constraints,
)
from shared_library.model_factory.registry_loader import RegistryBundle, load_registries
from shared_library.model_factory.resolver import (
    ModelFactoryResolver,
    resolve_chat_model,
)
from shared_library.model_factory.usage_patch import install_usage_dedup_patch

# Install the usage deduplication patch once at import time.
# This patches ChatOpenAI._stream and _astream to filter input_tokens on non-final chunks,
# preventing 50x+ inflation when the AI Gateway repeats usage_metadata on every SSE chunk.
install_usage_dedup_patch()

__all__ = [
    "AuthBridgeError",
    "ConstraintAwareChatModel",
    "FamilyPolicy",
    "GatewayCredentials",
    "MessageConstraints",
    "ModelFactoryError",
    "ModelFactoryResolver",
    "RegistryBundle",
    "RegistryError",
    "ResolveError",
    "adapt_messages_for_family",
    "adapt_messages_for_invoke",
    "build_request_params",
    "flatten_content_to_text",
    "get_message_constraints",
    "get_model_catalog",
    "invoke_model",
    "list_models",
    "list_profiles",
    "load_registries",
    "peek_resolved_model_key",
    "peek_resolved_model_label",
    "resolve_chat_model",
    "resolve_family_policy",
    "resolve_gateway_credentials",
    "wrap_with_message_constraints",
]

