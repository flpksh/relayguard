from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.organization import OrganizationResponse
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    organization_slug: str = Field(
        min_length=2, max_length=63, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("organization_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("o nome da organização deve ter pelo menos 2 caracteres")
        return normalized

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a senha não pode conter somente espaços")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrganizationResponse
