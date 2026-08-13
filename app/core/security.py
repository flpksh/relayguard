from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

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


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def create_access_token(user_id: UUID, organization_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": uuid4().hex,
    }
    return jwt.encode(
        payload,
        settings.access_token_secret.get_secret_value(),
        algorithm=settings.access_token_algorithm,
    )


def decode_access_token(token: str) -> TokenClaims | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.access_token_secret.get_secret_value(),
            algorithms=[settings.access_token_algorithm],
            options={"require": ["sub", "org", "iat", "exp", "jti"]},
        )
        return TokenClaims(
            user_id=UUID(payload["sub"]),
            organization_id=UUID(payload["org"]),
        )
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        return None
