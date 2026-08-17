"""Posts service object for the /posts endpoint."""
from __future__ import annotations

from typing import Any, Mapping

from framework.client.response import ApiResponse
from framework.core.base_service import BaseService


class PostsService(BaseService):
    service_key = "posts"

    def list_posts(self, **params: Any) -> ApiResponse:
        return self.get(params=params or None)

    def get_post(self, post_id: int | str) -> ApiResponse:
        return self.get(str(post_id))

    def posts_by_user(self, user_id: int | str) -> ApiResponse:
        return self.get(params={"userId": user_id})

    def create_post(self, payload: Mapping[str, Any]) -> ApiResponse:
        return self.post(json=dict(payload))

    def update_post(self, post_id: int | str, payload: Mapping[str, Any]) -> ApiResponse:
        return self.put(str(post_id), json=dict(payload))

    def delete_post(self, post_id: int | str) -> ApiResponse:
        return self.delete(str(post_id))
