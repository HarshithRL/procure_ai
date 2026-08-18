"""YAML-driven catalog of profiles and models for UI / API consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from shared_library.model_factory.family_adapter import is_chat_routable
from shared_library.model_factory.registry_loader import RegistryBundle, load_registries

_EFFORT_MAP = {
    "low": "fast_chat",
    "medium": "balanced",
    "high": "deep_reasoning",
}

_TIER_BADGES = {
    "fast": "Fast",
    "workhorse": "Medium",
    "frontier": "High",
    "open_frontier": "High",
    "throughput": "Medium",
    "small": "Fast",
}

_VENDOR_PREFIXES = (
    "Anthropic ",
    "OpenAI ",
    "Meta ",
    "Google ",
    "Alibaba ",
)

_HIDDEN_STATUSES = {"superseded", "deprecated", "retired"}
_VALID_SURFACES = {"chat", "power_user", "all"}


def _humanize(model_id: str) -> str:
    name = model_id
    if name.startswith("system.ai."):
        name = name[len("system.ai.") :]
    return name.replace("-", " ").title()


def _short_name(display: str, model_id: str) -> str:
    name = display.strip() if display else ""
    for prefix in _VENDOR_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    if not name:
        name = _humanize(model_id)
    return name


def _normalize_surface(surface: Optional[str]) -> str:
    key = (surface or "chat").strip().lower() or "chat"
    if key not in _VALID_SURFACES:
        return "chat"
    return key


def _is_embedding(meta: Dict[str, Any]) -> bool:
    return "embed" in str(meta.get("task") or "").lower()


def _chat_eligible(meta: Dict[str, Any]) -> bool:
    if _is_embedding(meta):
        return False
    status = str(meta.get("status") or "").lower()
    if status in _HIDDEN_STATUSES:
        return False
    return is_chat_routable(meta)


def _picker_visible(meta: Dict[str, Any], surface: str) -> bool:
    if surface == "all":
        return True
    return _chat_eligible(meta)


def _badges_for(meta: Dict[str, Any]) -> List[str]:
    badges: list[str] = []
    tier = str(meta.get("tier") or "")
    if tier in _TIER_BADGES:
        badges.append(_TIER_BADGES[tier])
    if meta.get("reasoning_mode") in {"thinking", "reasoning_effort", "forced"}:
        badges.append("Reasoning")
    if meta.get("temperature_supported") is False:
        badges.append("No temp")
    caps = meta.get("capabilities") or []
    if isinstance(caps, list) and "tool_calling" in caps:
        badges.append("Tools")
    status = str(meta.get("status") or "")
    if status in {"public_preview", "preview"}:
        badges.append("Preview")
    seen: set[str] = set()
    out: list[str] = []
    for b in badges:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


def list_profiles(
    registries_dir: Optional[Path | str] = None,
    bundle: Optional[RegistryBundle] = None,
    *,
    surface: str = "all",
) -> List[Dict[str, Any]]:
    """Return UI-safe profile entries from ProfileRegistry."""
    data = bundle or load_registries(registries_dir)
    surface_key = _normalize_surface(surface) if surface != "all" else "all"
    out: List[Dict[str, Any]] = []
    for profile_id, meta in data.profiles.items():
        if not isinstance(meta, dict):
            continue
        surfaces = [str(s) for s in (meta.get("surfaces") or []) if s]
        if surface_key != "all" and surface_key not in surfaces:
            continue
        default_model = meta.get("default_model") or meta.get("primary")
        model_meta = data.models.get(str(default_model)) if default_model else None
        default_label = ""
        if isinstance(model_meta, dict):
            display = str(model_meta.get("display_name") or _humanize(str(default_model)))
            default_label = _short_name(display, str(default_model))
        elif default_model:
            default_label = _humanize(str(default_model))
        out.append(
            {
                "id": profile_id,
                "label": str(meta.get("label") or profile_id.replace("_", " ").title()),
                "description": str(meta.get("description") or ""),
                "effort": meta.get("effort"),
                "surfaces": surfaces,
                "default_model": default_model,
                "default_model_label": default_label,
                "fallback_model": meta.get("fallback_model"),
                "fallbacks": meta.get("fallbacks") or [],
                "requires": meta.get("requires") or [],
                "default_hyperparameters": meta.get("default_hyperparameters") or {},
            }
        )
    return out


def list_models(
    registries_dir: Optional[Path | str] = None,
    bundle: Optional[RegistryBundle] = None,
    *,
    surface: str = "all",
) -> List[Dict[str, Any]]:
    """Return UI-safe model entries from ModelRegistry (``system.ai.*``)."""
    data = bundle or load_registries(registries_dir)
    surface_key = _normalize_surface(surface) if surface != "all" else "all"
    out: List[Dict[str, Any]] = []
    for model_id, meta in data.models.items():
        if not isinstance(meta, dict):
            continue
        if not _picker_visible(meta, surface_key):
            continue
        physical = meta.get("physical_model") or model_id
        display = meta.get("display_name") or _humanize(str(physical))
        task = str(meta.get("task") or "llm/v1/chat")
        swap_safe = bool(meta.get("swap_safe_for_agent", True))
        if "embed" in task.lower():
            swap_safe = False
        caps = meta.get("capabilities") or []
        if not isinstance(caps, list):
            caps = []
        out.append(
            {
                "id": model_id,
                "label": str(display),
                "display_name": str(display),
                "short_name": _short_name(str(display), str(model_id)),
                "physical_model": physical,
                "endpoint": meta.get("endpoint"),
                "provider_ref": meta.get("provider_ref"),
                "family": meta.get("family"),
                "tier": meta.get("tier"),
                "task": task,
                "temperature_supported": bool(meta.get("temperature_supported", True)),
                "reasoning_mode": meta.get("reasoning_mode") or "none",
                "swap_safe_for_agent": swap_safe,
                "routable": bool(meta.get("routable", True)),
                "chat_eligible": _chat_eligible(meta),
                "status": meta.get("status"),
                "capabilities": caps,
                "superseded_by": meta.get("superseded_by"),
                "badges": _badges_for(meta),
            }
        )
    return out


def peek_resolved_model_key(
    profile: str,
    model: Optional[str] = None,
    *,
    registries_dir: Optional[Path | str] = None,
) -> str:
    """Return the physical ``system.ai.*`` id a profile/override would bind."""
    explicit = (model or "").strip()
    if explicit:
        return explicit
    data = load_registries(registries_dir)
    meta = data.profiles.get(profile or "fast_chat") or {}
    if not isinstance(meta, dict):
        return ""
    return str(meta.get("default_model") or meta.get("primary") or "")


def peek_resolved_model_label(
    profile: str,
    model: Optional[str] = None,
    *,
    registries_dir: Optional[Path | str] = None,
) -> str:
    """Human short name for the model ``peek_resolved_model_key`` would bind."""
    model_id = peek_resolved_model_key(
        profile, model, registries_dir=registries_dir
    )
    if not model_id:
        return ""
    data = load_registries(registries_dir)
    meta = data.models.get(model_id) or {}
    if isinstance(meta, dict):
        display = str(meta.get("display_name") or _humanize(model_id))
        return _short_name(display, model_id)
    return _humanize(model_id)


def get_model_catalog(
    registries_dir: Optional[Path | str] = None,
    *,
    surface: str = "chat",
) -> Dict[str, Any]:
    """Combined catalog payload for ``GET /model-catalog``."""
    surface_key = _normalize_surface(surface)
    bundle = load_registries(registries_dir)
    return {
        "schema_version": 3,
        "surface": surface_key,
        "defaults": {
            "profile": "fast_chat",
            "effort": "low",
            "fast": False,
        },
        "effort_map": dict(_EFFORT_MAP),
        "fast_profile": "fast_chat",
        "profiles": list_profiles(bundle=bundle, surface=surface_key),
        "models": list_models(bundle=bundle, surface=surface_key),
    }

