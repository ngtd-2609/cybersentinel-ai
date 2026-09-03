import re
import string

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


class EmailMixin(BaseModel):
    email: str = Field(min_length=3, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()

        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid email address")

        return normalized


class UserCreate(EmailMixin):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip()

        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Username may contain only letters, numbers, dots, hyphens, and underscores"
            )

        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        requirements = (
            any(character.islower() for character in value),
            any(character.isupper() for character in value),
            any(character.isdigit() for character in value),
            any(character in string.punctuation for character in value),
        )

        if not all(requirements):
            raise ValueError(
                "Password must include uppercase, lowercase, number, and special character"
            )

        return value


class UserLogin(EmailMixin):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    role: str

    model_config = ConfigDict(from_attributes=True)
