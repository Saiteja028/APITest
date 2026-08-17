"""Environment-aware settings.

Load order (later wins):
  1. YAML file for the selected environment (config/environments/<TEST_ENV>.yaml)
  2. Matching environment variables (see .env.example)

A single immutable ``Settings`` object is exposed via ``get_settings()`` and
cached so the whole test session shares one consistent configuration.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Load .env early so os.getenv() sees developer overrides.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

_ENV_DIR = _PROJECT_ROOT / "config" / "environments"


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AuthConfig:
    strategy: str = "none"          # none | bearer | basic | api_key
    token: str = ""
    username: str = ""
    password: str = ""
    api_key_header: str = "X-API-Key"
    api_key: str = ""


@dataclass(frozen=True)
class Settings:
    env: str
    base_url: str
    timeout_ms: int
    ignore_https_errors: bool
    log_level: str
    default_headers: Dict[str, str] = field(default_factory=dict)
    services: Dict[str, str] = field(default_factory=dict)
    auth: AuthConfig = field(default_factory=AuthConfig)

    def service_path(self, name: str) -> str:
        """Return the configured base path for a named service."""
        try:
            return self.services[name]
        except KeyError as exc:
            raise KeyError(
                f"Service '{name}' is not configured for env '{self.env}'. "
                f"Known services: {sorted(self.services)}"
            ) from exc


def _load_yaml(env: str) -> Dict[str, Any]:
    path = _ENV_DIR / f"{env}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in _ENV_DIR.glob("*.yaml"))
        raise FileNotFoundError(
            f"No config file for env '{env}' at {path}. Available: {available}"
        )
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _build_settings() -> Settings:
    env = os.getenv("TEST_ENV", "dev").strip().lower()
    raw = _load_yaml(env)

    raw_auth = raw.get("auth", {}) or {}
    auth = AuthConfig(
        strategy=os.getenv("AUTH_STRATEGY", raw_auth.get("strategy", "none")),
        token=os.getenv("API_TOKEN", raw_auth.get("token", "")),
        username=os.getenv("API_USERNAME", raw_auth.get("username", "")),
        password=os.getenv("API_PASSWORD", raw_auth.get("password", "")),
        api_key_header=raw_auth.get("api_key_header", "X-API-Key"),
        api_key=os.getenv("API_KEY", raw_auth.get("api_key", "")),
    )

    return Settings(
        env=raw.get("name", env),
        base_url=(os.getenv("API_BASE_URL") or raw.get("base_url", "")).rstrip("/"),
        timeout_ms=int(os.getenv("HTTP_TIMEOUT_MS", raw.get("timeout_ms", 30000))),
        ignore_https_errors=_as_bool(
            os.getenv("IGNORE_HTTPS_ERRORS"), raw.get("ignore_https_errors", False)
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        default_headers=dict(raw.get("default_headers", {})),
        services=dict(raw.get("services", {})),
        auth=auth,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached, immutable settings for the active environment."""
    return _build_settings()
