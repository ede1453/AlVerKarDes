from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt


class TokenValidationError(ValueError):
    pass


class TokenCodec:
    def __init__(
        self,
        *,
        secret: str,
        algorithm: str,
        issuer: str,
        audience: str,
        access_minutes: int,
    ) -> None:
        self.secret = secret
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.access_minutes = access_minutes

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    def encode_access_token(
        self,
        *,
        user_id: str,
        session_id: str,
        security_version: int,
        extra_claims: dict[str, Any] | None = None,
    ) -> tuple[str, datetime]:
        now = self.now()
        expires_at = now + timedelta(
            minutes=self.access_minutes
        )

        payload: dict[str, Any] = {
            "sub": user_id,
            "sid": session_id,
            "sv": security_version,
            "jti": str(uuid4()),
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "typ": "access",
        }
        payload.update(extra_claims or {})

        return (
            jwt.encode(
                payload,
                self.secret,
                algorithm=self.algorithm,
            ),
            expires_at,
        )

    def decode_access_token(
        self,
        token: str,
    ) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
            )
        except JWTError as exc:
            raise TokenValidationError(
                "ACCESS_TOKEN_INVALID"
            ) from exc

        required = {
            "sub",
            "sid",
            "sv",
            "jti",
            "iss",
            "aud",
            "exp",
            "typ",
        }

        if not required.issubset(payload):
            raise TokenValidationError(
                "ACCESS_TOKEN_CLAIMS_MISSING"
            )

        if payload.get("typ") != "access":
            raise TokenValidationError(
                "ACCESS_TOKEN_TYPE_INVALID"
            )

        return payload


def create_opaque_token() -> str:
    return token_urlsafe(64)


def hash_opaque_token(token: str) -> str:
    return sha256(
        token.encode("utf-8")
    ).hexdigest()
