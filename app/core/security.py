from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings

password_hasher = PasswordHasher()


@dataclass(frozen=True)
class TokenClaims:
    user_id: UUID
    organization_id: UUID
    token_version: int


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def create_access_token(
    user_id: UUID, organization_id: UUID, token_version: int
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "iss": settings.access_token_issuer,
        "aud": settings.access_token_audience,
        "ver": token_version,
    }
    return jwt.encode(
        payload,
        settings.access_token_secret.get_secret_value(),
        algorithm=settings.access_token_algorithm,
    )


def decode_access_token(token: str) -> TokenClaims | None:
    settings = get_settings()
    secrets = [settings.access_token_secret.get_secret_value()]
    if settings.access_token_previous_secret is not None:
        secrets.append(settings.access_token_previous_secret.get_secret_value())
    for secret in secrets:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.access_token_algorithm],
                audience=settings.access_token_audience,
                issuer=settings.access_token_issuer,
                options={"require": ["sub", "org", "iat", "exp", "iss", "aud", "ver"]},
            )
            token_version = payload["ver"]
            if not isinstance(token_version, int) or token_version < 0:
                return None
            return TokenClaims(
                user_id=UUID(payload["sub"]),
                organization_id=UUID(payload["org"]),
                token_version=token_version,
            )
        except (InvalidTokenError, KeyError, TypeError, ValueError):
            continue
    return None
