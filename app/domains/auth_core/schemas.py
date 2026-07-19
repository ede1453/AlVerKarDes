from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)
    device_name: str | None = Field(default=None, max_length=255)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=2048)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(
        default=None,
        min_length=32,
        max_length=2048,
    )
    all_sessions: bool = False


class EmailVerificationIssueRequest(BaseModel):
    user_id: UUID


class EmailVerificationConfirmRequest(BaseModel):
    token: str = Field(min_length=32, max_length=2048)


class PasswordResetIssueRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=32, max_length=2048)
    new_password: str = Field(min_length=12, max_length=1024)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    device_name: str | None
    ip_address: str | None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime
    session_id: UUID


class AuthenticationResponse(BaseModel):
    authenticated: bool
    reason: str | None = None
    user_id: UUID | None = None
    tokens: TokenPairResponse | None = None


class MessageResponse(BaseModel):
    success: bool
    message: str
