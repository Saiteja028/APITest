"""Pluggable authentication.

Translates an ``AuthConfig`` into the HTTP headers required by the target API.
Supported strategies:
  - none    : no auth headers
  - bearer  : Authorization: Bearer <token>
  - basic   : Authorization: Basic <base64(user:pass)>
  - api_key : <configured header>: <api_key>

Extend by adding a new branch (or a new handler) here; nothing else in the
framework needs to change.
"""
from __future__ import annotations

import base64
from typing import Dict

from config.settings import AuthConfig


def build_auth_headers(auth: AuthConfig) -> Dict[str, str]:
    strategy = (auth.strategy or "none").strip().lower()

    if strategy == "none":
        return {}

    if strategy == "bearer":
        if not auth.token:
            raise ValueError("Bearer auth selected but no token provided (API_TOKEN).")
        return {"Authorization": f"Bearer {auth.token}"}

    if strategy == "basic":
        if not (auth.username and auth.password):
            raise ValueError("Basic auth selected but username/password missing.")
        raw = f"{auth.username}:{auth.password}".encode("utf-8")
        return {"Authorization": f"Basic {base64.b64encode(raw).decode('ascii')}"}

    if strategy == "api_key":
        if not auth.api_key:
            raise ValueError("api_key auth selected but no api_key provided (API_KEY).")
        return {auth.api_key_header: auth.api_key}

    raise ValueError(f"Unknown auth strategy: '{auth.strategy}'")
