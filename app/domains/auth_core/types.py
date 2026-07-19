from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class AuthSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    COMPROMISED = "COMPROMISED"


class AuthTokenPurpose(StrEnum):
    REFRESH = "REFRESH"
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"


class AuthEventType(StrEnum):
    LOGIN_SUCCEEDED = "LOGIN_SUCCEEDED"
    LOGIN_FAILED = "LOGIN_FAILED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_REVOKED = "SESSION_REVOKED"
    REFRESH_ROTATED = "REFRESH_ROTATED"
    REFRESH_REUSE_DETECTED = "REFRESH_REUSE_DETECTED"
    EMAIL_VERIFICATION_ISSUED = "EMAIL_VERIFICATION_ISSUED"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"
    PASSWORD_RESET_ISSUED = "PASSWORD_RESET_ISSUED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"


@dataclass(frozen=True)
class AuthContext:
    ip_address: str | None = None
    user_agent: str | None = None
    device_name: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    session_id: str


@dataclass(frozen=True)
class AuthenticationResult:
    authenticated: bool
    reason: str | None = None
    user_id: str | None = None
    token_pair: TokenPair | None = None
    metadata: dict[str, Any] | None = None
