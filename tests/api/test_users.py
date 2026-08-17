"""Users service tests.

Demonstrates the framework end-to-end: service objects, fluent assertions,
schema-contract validation, data-driven cases, and negative paths.
"""
from __future__ import annotations

import pytest

from framework.utils.data_loader import load_json
from framework.utils.schema_validator import validate_schema
from services.users_service import UsersService


@pytest.mark.smoke
@pytest.mark.users
def test_list_users_returns_collection(users: UsersService) -> None:
    data = users.list_users().expect_ok().expect_json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.smoke
@pytest.mark.users
@pytest.mark.schema
def test_get_user_matches_schema(users: UsersService) -> None:
    user = users.get_user(1).expect_status(200).expect_json()
    assert user["id"] == 1
    validate_schema(user, "user_schema.json")


@pytest.mark.users
@pytest.mark.schema
def test_every_user_matches_schema(users: UsersService) -> None:
    for user in users.list_users().expect_ok().expect_json():
        validate_schema(user, "user_schema.json")


@pytest.mark.users
@pytest.mark.parametrize("user_id", [1, 2, 5, 10])
def test_get_user_by_id(users: UsersService, user_id: int) -> None:
    user = users.get_user(user_id).expect_ok().expect_json()
    assert user["id"] == user_id


@pytest.mark.users
def test_create_user_from_data_file(users: UsersService) -> None:
    payload = load_json("new_user.json")
    resp = users.create_user(payload).expect_status(201)
    body = resp.expect_json()
    assert body["name"] == payload["name"]
    # JSONPlaceholder echoes back a generated id on create.
    assert "id" in body


@pytest.mark.users
def test_update_user(users: UsersService) -> None:
    resp = users.update_user(1, {"name": "Updated Name", "username": "updated"})
    body = resp.expect_ok().expect_json()
    assert body["name"] == "Updated Name"


@pytest.mark.negative
@pytest.mark.users
def test_get_missing_user_returns_404(users: UsersService) -> None:
    users.get_user(99999).expect_status(404)


@pytest.mark.users
def test_response_latency_is_reasonable(users: UsersService) -> None:
    resp = users.get_user(1).expect_ok()
    assert resp.elapsed_ms < 10000, f"Request too slow: {resp.elapsed_ms}ms"
