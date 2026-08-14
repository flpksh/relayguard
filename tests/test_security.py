from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pytest import MonkeyPatch

from app.core import security
from app.core.config import Settings


def test_decode_accepts_previous_secret_during_rotation(
    monkeypatch: MonkeyPatch,
) -> None:
    current_secret = "current-secret-with-at-least-thirty-two-characters"
    previous_secret = "previous-secret-with-at-least-thirty-two-characters"
    settings = Settings(
        _env_file=None,
        access_token_secret=current_secret,
        access_token_previous_secret=previous_secret,
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    now = datetime.now(UTC)
    user_id = uuid4()
    organization_id = uuid4()
    token = jwt.encode(
        {
            "sub": str(user_id),
            "org": str(organization_id),
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": settings.access_token_issuer,
            "aud": settings.access_token_audience,
            "ver": 3,
        },
        previous_secret,
        algorithm=settings.access_token_algorithm,
    )

    claims = security.decode_access_token(token)

    assert claims is not None
    assert claims.user_id == user_id
    assert claims.organization_id == organization_id
    assert claims.token_version == 3


def test_rejects_token_without_expected_audience(monkeypatch: MonkeyPatch) -> None:
    settings = Settings(_env_file=None)
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    token = jwt.encode(
        {"sub": str(uuid4()), "org": str(uuid4()), "ver": 0},
        settings.access_token_secret.get_secret_value(),
        algorithm=settings.access_token_algorithm,
    )

    assert security.decode_access_token(token) is None
