from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient

from app.core.config import get_settings
from app.database.session import session_factory
from app.repositories.user import UserRepository
from tests.test_identity import register


async def test_rejects_duplicate_email_and_rolls_back_registration(
    client: AsyncClient,
) -> None:
    await register(client, "email-original")
    duplicate = await client.post(
        "/auth/register",
        json={
            "organization_name": "Outra organização",
            "organization_slug": "test-email-duplicate",
            "email": "owner-email-original@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "o e-mail já existe"}

    retry = await client.post(
        "/auth/register",
        json={
            "organization_name": "Outra organização",
            "organization_slug": "test-email-duplicate",
            "email": "owner-email-retry@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert retry.status_code == 201


async def test_rejects_blank_organization_names_and_passwords(
    client: AsyncClient,
) -> None:
    blank_name = await client.post(
        "/auth/register",
        json={
            "organization_name": "  ",
            "organization_slug": "test-blank-name",
            "email": "blank-name@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    blank_password = await client.post(
        "/auth/register",
        json={
            "organization_name": "Organização válida",
            "organization_slug": "test-blank-password",
            "email": "blank-password@example.com",
            "password": "            ",
        },
    )

    assert blank_name.status_code == 422
    assert blank_password.status_code == 422
    assert blank_name.json()["detail"] == "dados da requisição inválidos"


async def test_rejects_blank_organization_rename(client: AsyncClient) -> None:
    _, headers = await register(client, "blank-rename")

    response = await client.patch(
        "/organizations/current", json={"name": "  "}, headers=headers
    )

    assert response.status_code == 422


async def test_logout_revokes_existing_token(client: AsyncClient) -> None:
    _, headers = await register(client, "logout")

    logout = await client.post("/auth/logout", headers=headers)
    after_logout = await client.get("/auth/me", headers=headers)

    assert logout.status_code == 204
    assert after_logout.status_code == 401


async def test_inactive_user_cannot_use_existing_token(client: AsyncClient) -> None:
    _, headers = await register(client, "inactive")
    async with session_factory() as session:
        user = await UserRepository.get_by_email(session, "owner-inactive@example.com")
        assert user is not None
        user.is_active = False
        await session.commit()

    response = await client.get("/auth/me", headers=headers)

    assert response.status_code == 401


async def test_rejects_expired_and_malformed_tokens(client: AsyncClient) -> None:
    body, _ = await register(client, "expired")
    settings = get_settings()
    now = datetime.now(UTC)
    user = body["user"]
    organization = body["organization"]
    assert isinstance(user, dict)
    assert isinstance(organization, dict)
    expired = jwt.encode(
        {
            "sub": user["id"],
            "org": organization["id"],
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
            "iss": settings.access_token_issuer,
            "aud": settings.access_token_audience,
            "ver": 0,
        },
        settings.access_token_secret.get_secret_value(),
        algorithm=settings.access_token_algorithm,
    )

    expired_response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )
    malformed_response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalido"}
    )

    assert expired_response.status_code == 401
    assert malformed_response.status_code == 401


async def test_user_listing_supports_pagination(client: AsyncClient) -> None:
    _, headers = await register(client, "pagination")
    for index in range(2):
        response = await client.post(
            "/users",
            json={
                "email": f"member-{index}-pagination@example.com",
                "password": "member-password-is-long",
            },
            headers=headers,
        )
        assert response.status_code == 201

    first_page = await client.get("/users?limit=1&offset=0", headers=headers)
    second_page = await client.get("/users?limit=1&offset=1", headers=headers)

    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["email"] != second_page.json()[0]["email"]


async def test_login_rate_limit(client: AsyncClient) -> None:
    responses = []
    for index in range(11):
        responses.append(
            await client.post(
                "/auth/login",
                json={
                    "email": f"missing-{index}@example.com",
                    "password": "wrong",
                },
            )
        )

    assert all(response.status_code == 401 for response in responses[:10])
    assert responses[10].status_code == 429
    assert "Retry-After" in responses[10].headers
