"""High-level HTTP client wrapping Playwright's ``APIRequestContext``.

Responsibilities:
  - Own the lifecycle of the Playwright request context.
  - Merge default headers + auth headers on every request.
  - Normalize relative paths against the configured base URL.
  - Log every request/response and measure latency.
  - Return the framework's :class:`ApiResponse` wrapper.

Usage::

    with ApiClient.create() as client:
        resp = client.get("/users/1").expect_ok()
"""
from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urljoin

from playwright.sync_api import APIRequestContext, sync_playwright

from config.settings import Settings, get_settings
from framework.auth.auth_provider import build_auth_headers
from framework.client.response import ApiResponse
from framework.core.logger import get_logger

_log = get_logger("api-client")

# Methods that carry a body.
_BODY_METHODS = {"post", "put", "patch", "delete"}


class ApiClient:
    def __init__(self, request_context: APIRequestContext, settings: Settings,
                 _playwright=None) -> None:
        self._ctx = request_context
        self._settings = settings
        self._playwright = _playwright  # kept only when self-managed

    # ---- Construction -----------------------------------------------------
    @classmethod
    def create(cls, settings: Optional[Settings] = None) -> "ApiClient":
        """Create a self-managed client (starts its own Playwright).

        Prefer the pytest fixtures for tests; use this for scripts/CLIs.
        """
        settings = settings or get_settings()
        pw = sync_playwright().start()
        ctx = pw.request.new_context(
            base_url=settings.base_url,
            extra_http_headers=cls._base_headers(settings),
            timeout=settings.timeout_ms,
            ignore_https_errors=settings.ignore_https_errors,
        )
        _log.info("ApiClient created for env='%s' base_url='%s'",
                  settings.env, settings.base_url)
        return cls(ctx, settings, _playwright=pw)

    @classmethod
    def from_context(cls, ctx: APIRequestContext,
                     settings: Optional[Settings] = None) -> "ApiClient":
        """Wrap an externally-owned request context (e.g. from a fixture)."""
        return cls(ctx, settings or get_settings())

    @staticmethod
    def _base_headers(settings: Settings) -> Dict[str, str]:
        headers = dict(settings.default_headers)
        headers.update(build_auth_headers(settings.auth))
        return headers

    # ---- HTTP verbs -------------------------------------------------------
    def get(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("get", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("post", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("put", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("patch", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("delete", path, **kwargs)

    # ---- Core -------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        **extra: Any,
    ) -> ApiResponse:
        url = self._resolve(path)
        call = getattr(self._ctx, method)

        request_kwargs: Dict[str, Any] = {}
        if params is not None:
            request_kwargs["params"] = dict(params)
        if headers is not None:
            request_kwargs["headers"] = dict(headers)
        if json is not None:
            request_kwargs["data"] = json  # Playwright serializes dict/list as JSON
        elif data is not None:
            request_kwargs["data"] = data
        request_kwargs.update(extra)

        _log.info("--> %s %s", method.upper(), url)
        if json is not None:
            _log.debug("    payload: %s", json)

        start = time.perf_counter()
        raw = call(url, **request_kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        _log.info("<-- %s %s [%s] %.0fms",
                  method.upper(), url, raw.status, elapsed_ms)
        return ApiResponse(raw, elapsed_ms)

    def _resolve(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        base = self._settings.base_url
        if not base:
            return path
        # urljoin needs a trailing slash on base to preserve the last segment.
        return urljoin(base + "/", path.lstrip("/"))

    # ---- Lifecycle --------------------------------------------------------
    def dispose(self) -> None:
        try:
            self._ctx.dispose()
        finally:
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.dispose()
