"""Base class for service objects.

A "service object" is the API equivalent of a page object: it encapsulates the
endpoints of one logical service so tests read as business actions rather than
raw HTTP calls. Subclasses declare a ``service_key`` that maps to a base path in
the environment config.
"""
from __future__ import annotations

from typing import Any

from framework.client.api_client import ApiClient
from framework.client.response import ApiResponse
from framework.core.logger import get_logger


class BaseService:
    #: Key looked up in Settings.services to find this service's base path.
    service_key: str = ""

    def __init__(self, client: ApiClient) -> None:
        self._client = client
        self._log = get_logger(f"service.{self.service_key or self.__class__.__name__}")

    @property
    def base_path(self) -> str:
        if not self.service_key:
            return ""
        return self._client._settings.service_path(self.service_key)

    def _path(self, suffix: str = "") -> str:
        base = self.base_path.rstrip("/")
        if not suffix:
            return base or "/"
        return f"{base}/{str(suffix).lstrip('/')}"

    # ---- Passthrough verbs scoped to this service's base path -------------
    def get(self, suffix: str = "", **kwargs: Any) -> ApiResponse:
        return self._client.get(self._path(suffix), **kwargs)

    def post(self, suffix: str = "", **kwargs: Any) -> ApiResponse:
        return self._client.post(self._path(suffix), **kwargs)

    def put(self, suffix: str = "", **kwargs: Any) -> ApiResponse:
        return self._client.put(self._path(suffix), **kwargs)

    def patch(self, suffix: str = "", **kwargs: Any) -> ApiResponse:
        return self._client.patch(self._path(suffix), **kwargs)

    def delete(self, suffix: str = "", **kwargs: Any) -> ApiResponse:
        return self._client.delete(self._path(suffix), **kwargs)
