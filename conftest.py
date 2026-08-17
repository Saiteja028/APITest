"""Session-wide pytest fixtures.

Fixture layering:
  settings (session)  -> immutable environment config
  api_context (session) -> one Playwright APIRequestContext for the whole run
  api_client (function) -> ApiClient wrapping that context
  <service> (function)  -> ready-to-use service objects

The request context is created once per session for speed; individual clients
are cheap wrappers around it.
"""
from __future__ import annotations

from typing import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import Settings, get_settings
from framework.auth.auth_provider import build_auth_headers
from framework.client.api_client import ApiClient
from framework.core.logger import get_logger
from services.posts_service import PostsService
from services.users_service import UsersService

_log = get_logger("conftest")


@pytest.fixture(scope="session")
def settings() -> Settings:
    cfg = get_settings()
    _log.info("Running test session against env='%s' base_url='%s'",
              cfg.env, cfg.base_url)
    return cfg


@pytest.fixture(scope="session")
def api_context(playwright: Playwright, settings: Settings) -> Iterator[APIRequestContext]:
    """A shared Playwright request context for the whole session.

    ``playwright`` is provided by the pytest-playwright plugin.
    """
    headers = dict(settings.default_headers)
    headers.update(build_auth_headers(settings.auth))

    context = playwright.request.new_context(
        base_url=settings.base_url,
        extra_http_headers=headers,
        timeout=settings.timeout_ms,
        ignore_https_errors=settings.ignore_https_errors,
    )
    yield context
    context.dispose()


@pytest.fixture()
def api_client(api_context: APIRequestContext, settings: Settings) -> ApiClient:
    return ApiClient.from_context(api_context, settings)


@pytest.fixture()
def users(api_client: ApiClient) -> UsersService:
    return UsersService(api_client)


@pytest.fixture()
def posts(api_client: ApiClient) -> PostsService:
    return PostsService(api_client)
