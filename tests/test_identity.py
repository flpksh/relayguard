from uuid import uuid4

import jwt
from httpx import AsyncClient

from app.core.config import get_settings


async def register(
    client: AsyncClient, suffix: str
) -> tuple[dict[str, object], dict[str, str]]:
    response = await client.post(
        "/auth/register",
        json={
            "organization_name": f" Test Organization {suffix} ",
            "organization_slug": f"test-{suffix}",
            "email": f"OWNER-{suffix}@EXAMPLE.COM",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body, {"Authorization": f"Bearer {body['access_token']}"}


async def test_registers_organization_and_owner_atomically(
    client: AsyncClient,
) -> None:
    body, headers = await register(client, "register")

    user = body["user"]
    organization = body["organization"]
    assert isinstance(user, dict)
    assert isinstance(organization, dict)
    assert user["email"] == "owner-register@example.com"
    assert user["role"] == "owner"
    assert user["organization_id"] == organization["id"]
    assert organization["name"] == "Test Organization register"
    assert organization["slug"] == "test-register"

    current = await client.get("/auth/me", headers=headers)
    assert current.status_code == 200
    assert current.json()["id"] == user["id"]


async def test_registration_rejects_duplicate_slug_or_email(
    client: AsyncClient,
) -> None:
    await register(client, "duplicate")
    response = await client.post(
        "/auth/register",
        json={
            "organization_name": "Another Organization",
            "organization_slug": "test-duplicate",
            "email": "another-duplicate@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 409


async def test_login_and_invalid_credentials(client: AsyncClient) -> None:
    registered, _ = await register(client, "login")
    response = await client.post(
        "/auth/login",
        json={
            "email": "owner-login@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 200
    assert response.json()["user"]["id"] == registered["user"]["id"]  # type: ignore[index]

    invalid = await client.post(
        "/auth/login",
        json={"email": "owner-login@example.com", "password": "wrong"},
    )
    assert invalid.status_code == 401
    assert invalid.json() == {"detail": "invalid email or password"}


async def test_owner_can_manage_organization_and_members(
    client: AsyncClient,
) -> None:
    _, owner_headers = await register(client, "management")

    renamed = await client.patch(
        "/organizations/current",
        json={"name": " Renamed Organization "},
        headers=owner_headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Renamed Organization"

    created = await client.post(
        "/users",
        json={
            "email": "member-management@example.com",
            "password": "member-password-is-long",
        },
        headers=owner_headers,
    )
    assert created.status_code == 201
    assert created.json()["role"] == "member"

    users = await client.get("/users", headers=owner_headers)
    assert users.status_code == 200
    assert [user["email"] for user in users.json()] == [
        "owner-management@example.com",
        "member-management@example.com",
    ]


async def test_member_cannot_perform_owner_operations(client: AsyncClient) -> None:
    _, owner_headers = await register(client, "authorization")
    await client.post(
        "/users",
        json={
            "email": "member-authorization@example.com",
            "password": "member-password-is-long",
        },
        headers=owner_headers,
    )
    login = await client.post(
        "/auth/login",
        json={
            "email": "member-authorization@example.com",
            "password": "member-password-is-long",
        },
    )
    member_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    add_member = await client.post(
        "/users",
        json={
            "email": "other-authorization@example.com",
            "password": "another-long-password",
        },
        headers=member_headers,
    )
    rename = await client.patch(
        "/organizations/current",
        json={"name": "Forbidden Rename"},
        headers=member_headers,
    )
    assert add_member.status_code == 403
    assert rename.status_code == 403


async def test_user_listing_is_isolated_by_organization(
    client: AsyncClient,
) -> None:
    _, first_headers = await register(client, "tenant-one")
    await register(client, "tenant-two")

    response = await client.get("/users", headers=first_headers)
    emails = [user["email"] for user in response.json()]
    assert emails == ["owner-tenant-one@example.com"]
    assert "owner-tenant-two@example.com" not in emails


async def test_rejects_token_with_mismatched_organization(
    client: AsyncClient,
) -> None:
    body, _ = await register(client, "token")
    settings = get_settings()
    token = jwt.decode(
        str(body["access_token"]),
        settings.access_token_secret.get_secret_value(),
        algorithms=[settings.access_token_algorithm],
    )
    token["org"] = str(uuid4())
    forged = jwt.encode(
        token,
        settings.access_token_secret.get_secret_value(),
        algorithm=settings.access_token_algorithm,
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401


async def test_protected_endpoint_requires_bearer_token(
    client: AsyncClient,
) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401
