"""Enterprise Model Factory resolver via LangChain ``init_chat_model``.

Routes chat traffic through Databricks Unity AI Gateway (OpenAI-compatible
``/ai-gateway/mlflow/v1``). Connection secrets (``api_key``, ``base_url``) are
sealed inside the resolver; only allowlisted sampling fields are configurable.
Family adapters strip illegal params and normalize message shapes on swap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from shared_library.databricks_connectors import AuthProvider, ConnectorHub

from shared_library.model_factory.auth_bridge import (
    GatewayCredentials,
    resolve_gateway_credentials,
)
from shared_library.model_factory.chat_model_wrapper import (
    wrap_with_message_constraints,
)
from shared_library.model_factory.exceptions import ResolveError
from shared_library.model_factory.family_adapter import (
    build_request_params,
    is_chat_routable,
    resolve_family_policy,
)
from shared_library.model_factory.registry_loader import RegistryBundle, load_registries

# Hardened allowlist — never include api_key / base_url / configurable_fields="any"
_CONFIGURABLE_FIELDS: List[str] = [
    "temperature",
    "max_tokens",
    "max_retries",
    "timeout",
]

_SAFE_OVERRIDE_KEYS = frozenset(_CONFIGURABLE_FIELDS)


class ModelFactoryResolver:
    """Resolve logical profiles / model aliases to a secured ``BaseChatModel``."""

    def __init__(
        self,
        registries_dir: Optional[Path | str] = None,
        *,
        hub: Optional[ConnectorHub] = None,
        provider: Optional[AuthProvider] = None,
        credentials: Optional[GatewayCredentials] = None,
    ) -> None:
        self._bundle: RegistryBundle = load_registries(registries_dir)
        self._hub = hub
        self._auth_provider = provider
        self._credentials = credentials

    @property
    def registries(self) -> RegistryBundle:
        return self._bundle

    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        profile = self._bundle.profiles.get(profile_name)
        if not isinstance(profile, dict):
            raise ResolveError(f"Profile '{profile_name}' is not registered")
        return profile

    def get_model_meta(self, model_key: str) -> Dict[str, Any]:
        meta = self._bundle.models.get(model_key)
        if not isinstance(meta, dict):
            for alias, candidate in self._bundle.models.items():
                if (
                    isinstance(candidate, dict)
                    and candidate.get("physical_model") == model_key
                ):
                    return candidate
            raise ResolveError(f"Model '{model_key}' is not registered")
        return meta

    def verify_capabilities(
        self,
        model_key: str,
        required_capabilities: Optional[Sequence[str]] = None,
    ) -> bool:
        """Return True if the model satisfies optional required feature flags."""
        if not required_capabilities:
            return model_key in self._bundle.capabilities or any(
                isinstance(m, dict) and m.get("physical_model") == model_key
                for m in self._bundle.models.values()
            )

        caps = self._bundle.capabilities.get(model_key)
        if not isinstance(caps, dict):
            # Resolve alias → capability key
            for alias, meta in self._bundle.models.items():
                if isinstance(meta, dict) and meta.get("physical_model") == model_key:
                    caps = self._bundle.capabilities.get(alias)
                    break
        if not isinstance(caps, dict):
            # Fall back to ModelRegistry capabilities list
            model = self.get_model_meta(model_key)
            listed = model.get("capabilities") or []
            if isinstance(listed, list):
                return all(name in listed for name in required_capabilities)
            return False

        features = caps.get("features") or {}
        supported_inputs = caps.get("supported_inputs") or []
        listed_caps = self.get_model_meta(model_key).get("capabilities") or []

        for name in required_capabilities:
            if name in ("text_input", "image_input"):
                modality = name.replace("_input", "")
                if modality in supported_inputs:
                    continue
            if name == "text_output":
                continue
            if name in ("extended_thinking", "forced_reasoning", "reasoning_effort"):
                if features.get("extended_thinking") or features.get("forced_reasoning"):
                    continue
                if features.get("reasoning_effort_control"):
                    continue
                if isinstance(listed_caps, list) and name in listed_caps:
                    continue
                return False
            if name in ("streaming", "system_prompt", "very_long_context"):
                if isinstance(listed_caps, list) and name in listed_caps:
                    continue
                # Advisory: allow if chat model
                continue
            if name == "structured_output":
                feat = features.get("structured_outputs") or features.get(
                    "structured_output"
                )
                if isinstance(feat, dict) and feat.get("supported"):
                    continue
                if feat is True:
                    continue
                return False
            if name == "tool_calling":
                feat = features.get("tool_calling")
                if isinstance(feat, dict) and feat.get("supported"):
                    continue
                if feat is True:
                    continue
                return False

            feature = features.get(name) if isinstance(features, dict) else None
            if isinstance(feature, dict):
                if not feature.get("supported", False):
                    return False
            elif feature:
                continue
            elif isinstance(listed_caps, list) and name in listed_caps:
                continue
            else:
                return False
        return True

    def _credentials_or_resolve(
        self,
        workspace_client: Any = None,
    ) -> GatewayCredentials:
        if self._credentials is not None:
            return self._credentials
        return resolve_gateway_credentials(
            hub=self._hub,
            provider=self._auth_provider,
            workspace_client=workspace_client,
        )

    def _resolve_model_key(
        self,
        profile_name: str,
        model: Optional[str] = None,
    ) -> str:
        if model:
            if model in self._bundle.models:
                return model
            for alias, meta in self._bundle.models.items():
                if isinstance(meta, dict) and meta.get("physical_model") == model:
                    return alias
            if model.startswith("system.ai."):
                return model
            raise ResolveError(f"Unknown model override '{model}'")

        profile = self.get_profile(profile_name)
        default_model = profile.get("default_model") or profile.get("primary")
        if not default_model or not isinstance(default_model, str):
            raise ResolveError(
                f"Profile '{profile_name}' missing string default_model/primary"
            )
        return default_model

    def _fallback_chain(self, profile: Dict[str, Any]) -> List[str]:
        chain: list[str] = []
        fb = profile.get("fallback_model")
        if isinstance(fb, str) and fb.strip():
            chain.append(fb.strip())
        fallbacks = profile.get("fallbacks")
        if isinstance(fallbacks, list):
            for item in fallbacks:
                if isinstance(item, str) and item.strip() and item not in chain:
                    chain.append(item.strip())
        return chain

    def _provider_meta(self, provider_ref: str) -> Dict[str, Any]:
        meta = self._bundle.providers.get(provider_ref)
        if not isinstance(meta, dict):
            raise ResolveError(f"Provider '{provider_ref}' is not registered")
        return meta

    def _merge_hyperparameters(
        self,
        *,
        model_meta: Dict[str, Any],
        profile: Dict[str, Any],
        overrides: Optional[Dict[str, Any]],
        temperature_supported: bool,
    ) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for source in (
            model_meta.get("default_parameters") or {},
            profile.get("default_hyperparameters") or {},
            overrides or {},
        ):
            if not isinstance(source, dict):
                continue
            for key, value in source.items():
                if key not in _SAFE_OVERRIDE_KEYS:
                    continue
                if value is None:
                    continue
                merged[key] = value

        if not temperature_supported:
            merged.pop("temperature", None)
        return merged

    def resolve(
        self,
        profile_name: str = "fast_chat",
        *,
        model: Optional[str] = None,
        required_capabilities: Optional[Sequence[str]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        config_prefix: Optional[str] = None,
        workspace_client: Any = None,
        enable_thinking: bool = False,
        reasoning_effort: Optional[str] = None,
    ) -> BaseChatModel:
        """Instantiate a secured chat model via ``init_chat_model``."""
        try:
            import mlflow
            from mlflow.entities import SpanType

            with mlflow.start_span(
                name="ModelFactoryResolver.resolve",
                span_type=SpanType.CHAIN,
            ) as span:
                span.set_inputs(
                    {
                        "profile": profile_name,
                        "model": model,
                        "required_capabilities": list(required_capabilities or []),
                    }
                )
                return self._resolve_impl(
                    profile_name,
                    model=model,
                    required_capabilities=required_capabilities,
                    overrides=overrides,
                    config_prefix=config_prefix,
                    workspace_client=workspace_client,
                    enable_thinking=enable_thinking,
                    reasoning_effort=reasoning_effort,
                    span=span,
                )
        except ImportError:
            return self._resolve_impl(
                profile_name,
                model=model,
                required_capabilities=required_capabilities,
                overrides=overrides,
                config_prefix=config_prefix,
                workspace_client=workspace_client,
                enable_thinking=enable_thinking,
                reasoning_effort=reasoning_effort,
                span=None,
            )

    def _resolve_impl(
        self,
        profile_name: str = "fast_chat",
        *,
        model: Optional[str] = None,
        required_capabilities: Optional[Sequence[str]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        config_prefix: Optional[str] = None,
        workspace_client: Any = None,
        enable_thinking: bool = False,
        reasoning_effort: Optional[str] = None,
        span: Any = None,
    ) -> BaseChatModel:
        profile = self.get_profile(profile_name)
        model_key = self._resolve_model_key(profile_name, model=model)
        req_caps = list(required_capabilities or [])
        if not req_caps:
            req = profile.get("requires")
            if isinstance(req, list):
                req_caps = [str(x) for x in req]

        def _try_key(key: str) -> bool:
            try:
                meta = self.get_model_meta(key)
            except ResolveError:
                return False
            if not is_chat_routable(meta):
                return False
            if req_caps and not self.verify_capabilities(key, req_caps):
                return False
            return True

        # Explicit model override: fail closed if not chat-routable (no silent fallback)
        if model:
            explicit_meta = self.get_model_meta(model_key)
            if not is_chat_routable(explicit_meta):
                raise ResolveError(
                    f"Model '{model_key}' is not chat-routable "
                    f"(task={explicit_meta.get('task')}, status={explicit_meta.get('status')})"
                )
            if req_caps and not self.verify_capabilities(model_key, req_caps):
                raise ResolveError(
                    f"Model '{model_key}' lacks required capabilities: {req_caps}"
                )
        elif not _try_key(model_key):
            chosen = None
            for fb in self._fallback_chain(profile):
                if _try_key(fb):
                    chosen = fb
                    break
            if chosen is None:
                meta = self.get_model_meta(model_key)
                if not is_chat_routable(meta):
                    raise ResolveError(
                        f"Model '{model_key}' is not chat-routable "
                        f"(task={meta.get('task')}, status={meta.get('status')})"
                    )
                raise ResolveError(
                    f"Model '{model_key}' lacks required capabilities: {req_caps}"
                )
            model_key = chosen

        model_meta = self.get_model_meta(model_key)
        if not is_chat_routable(model_meta):
            raise ResolveError(
                f"Model '{model_key}' cannot be bound as a chat model "
                f"(task={model_meta.get('task')})"
            )

        provider_ref = model_meta.get("provider_ref")
        if not isinstance(provider_ref, str):
            raise ResolveError(f"Model '{model_key}' missing provider_ref")

        provider_meta = self._provider_meta(provider_ref)
        model_provider = provider_meta.get("model_provider") or "openai"
        base_url = provider_meta.get("base_url")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ResolveError(
                f"Provider '{provider_ref}' missing base_url for AI Gateway"
            )

        physical_model = model_meta.get("physical_model") or model_key
        if not isinstance(physical_model, str):
            raise ResolveError(f"Model '{model_key}' has invalid physical_model")

        temperature_supported = bool(model_meta.get("temperature_supported", True))
        if "opus" in physical_model.lower():
            temperature_supported = False

        defaults = provider_meta.get("defaults") or {}
        if not isinstance(defaults, dict):
            defaults = {}

        hyperparams = self._merge_hyperparameters(
            model_meta=model_meta,
            profile=profile,
            overrides=overrides,
            temperature_supported=temperature_supported,
        )

        policy = resolve_family_policy(self._bundle, model_key)
        # Deep reasoning profiles enable Claude thinking by default
        think = enable_thinking or (
            profile_name == "deep_reasoning" and policy.reasoning_extra_body == "thinking"
        )
        effort = reasoning_effort
        if effort is None and policy.reasoning_extra_body == "reasoning_effort":
            effort = "low"

        filtered = build_request_params(
            policy=policy,
            temperature_supported=temperature_supported,
            merged_hyperparams=hyperparams,
            enable_thinking=think,
            reasoning_effort=effort,
        )
        extra_body = filtered.pop("extra_body", None)

        timeout = filtered.pop("timeout", None)
        max_retries = filtered.pop("max_retries", None)
        if timeout is None:
            timeout = defaults.get("timeout", 120)
        if max_retries is None:
            max_retries = defaults.get("max_retries", 3)

        creds = self._credentials_or_resolve(workspace_client=workspace_client)
        prefix = config_prefix if config_prefix is not None else profile_name

        if span is not None:
            try:
                from urllib.parse import urlparse

                host = urlparse(base_url).netloc if base_url else ""
                family = model_meta.get("family") or policy.family
                span.set_attributes(
                    {
                        "model_profile": profile_name,
                        "model_key": model_key,
                        "physical_model": physical_model,
                        "provider_ref": provider_ref,
                        "model_provider": model_provider,
                        "endpoint_host": host,
                        "model_family": str(family),
                        "tier": str(model_meta.get("tier") or ""),
                        "reasoning_mode": str(model_meta.get("reasoning_mode") or ""),
                        "endpoint": str(model_meta.get("endpoint") or ""),
                    }
                )
                span.set_outputs(
                    {
                        "model_key": model_key,
                        "physical_model": physical_model,
                        "provider_ref": provider_ref,
                        "endpoint_host": host,
                        "family": str(family),
                    }
                )
                try:
                    import mlflow

                    mlflow.update_current_trace(
                        tags={
                            "model": physical_model,
                            "family": str(family),
                            "tier": str(model_meta.get("tier") or ""),
                            "profile": profile_name,
                        }
                    )
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001
                pass

        init_kwargs: Dict[str, Any] = dict(filtered)
        if extra_body:
            init_kwargs["extra_body"] = extra_body

        try:
            chat = init_chat_model(
                model=physical_model,
                model_provider=model_provider,
                base_url=base_url.rstrip("/"),
                api_key=creds.api_key,
                configurable_fields=list(_CONFIGURABLE_FIELDS),
                config_prefix=prefix,
                timeout=timeout,
                max_retries=max_retries,
                **init_kwargs,
            )
        except Exception as exc:  # noqa: BLE001
            raise ResolveError(
                f"init_chat_model failed for '{physical_model}': {exc}"
            ) from exc

        return wrap_with_message_constraints(
            chat,
            model_key=model_key,
            bundle=self._bundle,
        )


def resolve_chat_model(
    profile: str = "fast_chat",
    *,
    model: Optional[str] = None,
    required_capabilities: Optional[Sequence[str]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    max_retries: Optional[int] = None,
    timeout: Optional[Union[int, float]] = None,
    config_prefix: Optional[str] = None,
    registries_dir: Optional[Path | str] = None,
    hub: Optional[ConnectorHub] = None,
    provider: Optional[AuthProvider] = None,
    workspace_client: Any = None,
    enable_thinking: bool = False,
    reasoning_effort: Optional[str] = None,
) -> BaseChatModel:
    """Module-level helper: resolve a profile/model to a ``BaseChatModel``."""
    overrides: Dict[str, Any] = {}
    if temperature is not None:
        overrides["temperature"] = temperature
    if max_tokens is not None:
        overrides["max_tokens"] = max_tokens
    if max_retries is not None:
        overrides["max_retries"] = max_retries
    if timeout is not None:
        overrides["timeout"] = timeout

    resolver = ModelFactoryResolver(
        registries_dir=registries_dir,
        hub=hub,
        provider=provider,
    )
    return resolver.resolve(
        profile,
        model=model,
        required_capabilities=required_capabilities,
        overrides=overrides or None,
        config_prefix=config_prefix,
        workspace_client=workspace_client,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
    )
