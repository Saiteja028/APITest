"""Posts service tests, including a cross-service workflow."""
from __future__ import annotations

import pytest

from framework.utils.schema_validator import validate_schema
from services.posts_service import PostsService
from services.users_service import UsersService


@pytest.mark.smoke
@pytest.mark.posts
def test_list_posts(posts: PostsService) -> None:
    data = posts.list_posts().expect_ok().expect_json()
    assert isinstance(data, list) and len(data) > 0


@pytest.mark.posts
@pytest.mark.schema
def test_get_post_matches_schema(posts: PostsService) -> None:
    post = posts.get_post(1).expect_ok().expect_json()
    validate_schema(post, "post_schema.json")


@pytest.mark.posts
def test_create_post(posts: PostsService) -> None:
    payload = {"title": "hello", "body": "world", "userId": 1}
    body = posts.create_post(payload).expect_status(201).expect_json()
    assert body["title"] == "hello"


@pytest.mark.regression
@pytest.mark.posts
def test_user_has_posts(users: UsersService, posts: PostsService) -> None:
    """Cross-service workflow: pick a user, then fetch their posts."""
    user = users.get_user(1).expect_ok().expect_json()
    user_posts = posts.posts_by_user(user["id"]).expect_ok().expect_json()
    assert len(user_posts) > 0
    assert all(p["userId"] == user["id"] for p in user_posts)
