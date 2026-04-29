from __future__ import annotations

import os
from typing import Any

from sqlalchemy.orm import Session

from apd.domain.models import AppSetting


DEFAULTS = {
    "provider": "ollama",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": None,
    "ollama_keep_alive": 0,
    "ollama_timeout_seconds": 120,
    "component_repair_attempts": 2,
    "enabled": True,
}

SETTING_KEY = "model_execution_settings"


def _parse_positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_nonnegative_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _load_from_db(db: Session) -> dict[str, Any] | None:
    row = db.query(AppSetting).filter(AppSetting.key == SETTING_KEY).first()
    if not row or not row.value_json:
        return None
    return dict(row.value_json)


def get_model_execution_settings(db: Session | None) -> dict[str, Any]:
    """Return merged settings: DB overrides env, then defaults."""
    result: dict[str, Any] = dict(DEFAULTS)
    # Load env as fallback first
    env_provider = (os.getenv("APD_MODEL_PROVIDER") or "").strip().lower()
    if env_provider:
        result["provider"] = env_provider
    env_base = (os.getenv("APD_OLLAMA_BASE_URL") or "").strip()
    if env_base:
        result["ollama_base_url"] = env_base
    env_model = (os.getenv("APD_OLLAMA_MODEL") or "").strip()
    if env_model:
        result["ollama_model"] = env_model
    env_timeout = os.getenv("APD_OLLAMA_TIMEOUT_SECONDS")
    if env_timeout:
        try:
            result["ollama_timeout_seconds"] = int(env_timeout)
        except Exception:
            pass
    env_keep = os.getenv("APD_OLLAMA_KEEP_ALIVE")
    if env_keep:
        try:
            result["ollama_keep_alive"] = int(env_keep)
        except Exception:
            result["ollama_keep_alive"] = env_keep
    env_rep = os.getenv("APD_COMPONENT_REPAIR_ATTEMPTS")
    if not env_rep:
        env_rep = os.getenv("APD_OLLAMA_REPAIR_ATTEMPTS")
    if env_rep:
        try:
            result["component_repair_attempts"] = min(int(env_rep), 3)
        except Exception:
            pass

    if db is None:
        return result

    db_value = _load_from_db(db)
    if db_value:
        # overlay DB values
        result.update({k: v for k, v in db_value.items() if v is not None})
    return result


def save_model_execution_settings(db: Session, data: dict[str, Any]) -> AppSetting:
    normalized = dict(DEFAULTS)
    normalized.update({k: v for k, v in data.items() if v is not None})
    normalized["provider"] = str(normalized.get("provider") or "").strip().lower() or "ollama"
    normalized["ollama_base_url"] = str(normalized.get("ollama_base_url") or "").strip() or None
    normalized["ollama_model"] = str(normalized.get("ollama_model") or "").strip() or None
    normalized["ollama_timeout_seconds"] = _parse_positive_int(normalized.get("ollama_timeout_seconds"), default=120)
    normalized["component_repair_attempts"] = min(
        _parse_nonnegative_int(normalized.get("component_repair_attempts"), default=1),
        3,
    )
    keep_alive = normalized.get("ollama_keep_alive")
    if isinstance(keep_alive, str):
        keep_alive = keep_alive.strip()
    try:
        normalized["ollama_keep_alive"] = int(keep_alive)
    except (TypeError, ValueError):
        normalized["ollama_keep_alive"] = keep_alive if keep_alive not in (None, "") else 0

    row = db.query(AppSetting).filter(AppSetting.key == SETTING_KEY).first()
    if row is None:
        row = AppSetting(key=SETTING_KEY, value_json=normalized)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    row.value_json = normalized
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def resolve_ollama_execution_config(db: Session | None = None) -> tuple[dict | None, list[str]]:
    """Resolve Ollama execution settings as a plain dict, using DB first, then env, then defaults.

    Returns (settings_dict, missing_list) where settings_dict is None if required values missing.
    """
    settings = get_model_execution_settings(db)
    provider = (settings.get("provider") or "").strip().lower()
    base_url = (settings.get("ollama_base_url") or "").strip()
    model = (settings.get("ollama_model") or "")

    missing: list[str] = []
    if provider != "ollama":
        missing.append("APD_MODEL_PROVIDER=ollama")
    if not base_url:
        missing.append("APD_OLLAMA_BASE_URL")
    if not model:
        missing.append("APD_OLLAMA_MODEL")

    if missing:
        return None, missing

    return (
        {
            "provider": provider,
            "ollama_base_url": base_url.rstrip("/"),
            "ollama_model": str(model),
            "ollama_timeout_seconds": _parse_positive_int(settings.get("ollama_timeout_seconds"), default=120),
            "component_repair_attempts": min(
                _parse_nonnegative_int(settings.get("component_repair_attempts"), default=1),
                3,
            ),
            "ollama_keep_alive": settings.get("ollama_keep_alive"),
        },
        [],
    )
