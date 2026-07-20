import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

# CLIENT-002h: kept in sync with frontend/i18n/routing.ts's `locales` --
# preferred_language is validated against exactly the locales next-intl
# actually serves (see ADR-015 for why this field doesn't force-redirect
# the active browsing session's URL locale, it's a backend/email-facing
# preference).
SUPPORTED_LOCALES = ("de", "en")


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str | None = None
    preferred_language: str = "en"
    preferred_currency: str = "EUR"
    preferred_country: str = "DE"


class UserProfileUpdateRequest(BaseModel):
    user_id: UUID
    display_name: str | None = Field(default=None, max_length=160)
    preferred_language: str = "en"
    preferred_country: str = "DE"

    @field_validator("preferred_language")
    @classmethod
    def _validate_preferred_language(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_LOCALES:
            raise ValueError(f"unsupported_locale, must be one of {SUPPORTED_LOCALES}")
        return normalized

    @field_validator("preferred_country")
    @classmethod
    def _validate_preferred_country(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", normalized):
            raise ValueError("invalid_country_code, must be a 2-letter ISO code")
        return normalized
