"""A thin, test-friendly wrapper around Playwright's ``APIResponse``.

Adds:
  - Lazy JSON / text parsing that never raises on empty bodies.
  - A fluent assertion surface (``expect_status``, ``expect_ok`` ...).
  - Convenience accessors (``ok``, ``elapsed_ms``, ``header``).
"""
from __future__ import annotations

import json
from typing import Any, Optional

from playwright.sync_api import APIResponse


class ApiResponse:
    def __init__(self, raw: APIResponse, elapsed_ms: float) -> None:
        self._raw = raw
        self._elapsed_ms = elapsed_ms
        self._body_bytes: Optional[bytes] = None
        self._json_cache: Any = _UNSET
        self._json_error: Optional[Exception] = None

    # ---- Basic properties -------------------------------------------------
    @property
    def status(self) -> int:
        return self._raw.status

    @property
    def status_text(self) -> str:
        return self._raw.status_text

    @property
    def ok(self) -> bool:
        return self._raw.ok

    @property
    def url(self) -> str:
        return self._raw.url

    @property
    def elapsed_ms(self) -> float:
        return round(self._elapsed_ms, 2)

    @property
    def headers(self) -> dict[str, str]:
        return self._raw.headers

    def header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self._raw.headers.get(name.lower(), default)

    # ---- Body accessors ---------------------------------------------------
    def body(self) -> bytes:
        if self._body_bytes is None:
            self._body_bytes = self._raw.body()
        return self._body_bytes

    def text(self) -> str:
        return self.body().decode("utf-8", errors="replace")

    def json(self) -> Any:
        """Parse the body as JSON. Returns ``None`` for empty bodies."""
        if self._json_cache is _UNSET:
            raw = self.text().strip()
            if not raw:
                self._json_cache = None
            else:
                try:
                    self._json_cache = json.loads(raw)
                except json.JSONDecodeError as exc:
                    self._json_cache = None
                    self._json_error = exc
        return self._json_cache

    # ---- Fluent assertions ------------------------------------------------
    def expect_status(self, expected: int) -> "ApiResponse":
        assert self.status == expected, (
            f"Expected status {expected} but got {self.status} "
            f"({self.status_text}) for {self.url}\nBody: {self._truncated_body()}"
        )
        return self

    def expect_ok(self) -> "ApiResponse":
        assert self.ok, (
            f"Expected a 2xx status but got {self.status} "
            f"({self.status_text}) for {self.url}\nBody: {self._truncated_body()}"
        )
        return self

    def expect_json(self) -> Any:
        data = self.json()
        assert self._json_error is None, (
            f"Response body was not valid JSON: {self._json_error}\n"
            f"Body: {self._truncated_body()}"
        )
        return data

    def expect_header(self, name: str, expected: str) -> "ApiResponse":
        actual = self.header(name)
        assert actual == expected, (
            f"Expected header '{name}' to be '{expected}' but got '{actual}'"
        )
        return self

    def _truncated_body(self, limit: int = 500) -> str:
        text = self.text()
        return text if len(text) <= limit else f"{text[:limit]}... [truncated]"

    def __repr__(self) -> str:
        return f"<ApiResponse {self.status} {self.url} ({self.elapsed_ms}ms)>"


class _Unset:
    """Sentinel so a cached JSON value of ``None`` is distinguishable."""


_UNSET = _Unset()
