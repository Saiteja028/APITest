"""Users service object.

Encapsulates all interactions with the /users endpoint so tests express intent
("create a user", "get user by id") instead of raw HTTP mechanics.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from framework.client.response import ApiResponse
from framework.core.base_service import BaseService


class UsersService(BaseService):
    service_key = "users"

    def list_users(self, **params: Any) -> ApiResponse:
        return self.get(params=params or None)

    def get_user(self, user_id: int | str) -> ApiResponse:
        return self.get(str(user_id))

    def create_user(self, payload: Mapping[str, Any]) -> ApiResponse:
        return self.post(json=dict(payload))

    def update_user(self, user_id: int | str, payload: Mapping[str, Any]) -> ApiResponse:
        return self.put(str(user_id), json=dict(payload))

    def patch_user(self, user_id: int | str, payload: Mapping[str, Any]) -> ApiResponse:
        return self.patch(str(user_id), json=dict(payload))

    def delete_user(self, user_id: int | str) -> ApiResponse:
        return self.delete(str(user_id))

    def find_by_username(self, username: str) -> Optional[dict]:
        """Return the first user matching ``username`` or ``None``."""
        resp = self.list_users(username=username).expect_ok()
        results = resp.expect_json()
        return results[0] if results else None
