from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# TEST-002 (2026-07-20): bcrypt's cost factor is a real production security
# control (default 12, ~250ms/hash -- deliberately expensive against
# offline cracking) but pure CPU waste in the test suite, where there is no
# real threat model for test-user passwords. settings.BCRYPT_ROUNDS
# defaults to 12 (production-safe, unchanged from before) -- only
# tests/conftest.py overrides it (via the BCRYPT_ROUNDS env var, set before
# any app import) to bcrypt's own minimum of 4 (~5ms/hash). Nothing about
# this touches DATABASE_URL/real-Postgres discipline; it only makes a
# CPU-bound hashing primitive cheaper for non-production use.
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
