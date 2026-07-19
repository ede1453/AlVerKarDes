from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth_core.models import (
    AccountSecurityState,
    AuthAuditEvent,
    AuthSession,
    AuthToken,
    LoginAttempt,
    PasswordHistory,
)


class AuthenticationCoreRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create_session(
        self,
        auth_session: AuthSession,
    ) -> AuthSession:
        self.session.add(auth_session)
        await self.session.flush()
        return auth_session

    async def get_session(
        self,
        session_id: UUID,
    ) -> AuthSession | None:
        return await self.session.get(
            AuthSession,
            session_id,
        )

    async def list_active_sessions(
        self,
        user_id: UUID,
        *,
        now: datetime,
    ) -> list[AuthSession]:
        result = await self.session.execute(
            select(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.status == "ACTIVE",
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .order_by(AuthSession.created_at.desc())
        )
        return list(result.scalars())

    async def revoke_session(
        self,
        session_id: UUID,
        *,
        revoked_at: datetime,
        reason: str,
        status: str = "REVOKED",
    ) -> bool:
        result = await self.session.execute(
            update(AuthSession)
            .where(
                AuthSession.id == session_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(
                status=status,
                revoked_at=revoked_at,
                revoke_reason=reason,
            )
        )
        return bool(result.rowcount)

    async def revoke_all_sessions(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
        reason: str,
        except_session_id: UUID | None = None,
    ) -> int:
        statement = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(
                status="REVOKED",
                revoked_at=revoked_at,
                revoke_reason=reason,
            )
        )

        if except_session_id is not None:
            statement = statement.where(
                AuthSession.id != except_session_id
            )

        result = await self.session.execute(statement)
        return int(result.rowcount or 0)

    async def create_token(
        self,
        token: AuthToken,
    ) -> AuthToken:
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_token_by_hash(
        self,
        token_hash: str,
    ) -> AuthToken | None:
        result = await self.session.execute(
            select(AuthToken).where(
                AuthToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    async def consume_token(
        self,
        token_id: UUID,
        *,
        consumed_at: datetime,
    ) -> bool:
        result = await self.session.execute(
            update(AuthToken)
            .where(
                AuthToken.id == token_id,
                AuthToken.consumed_at.is_(None),
                AuthToken.revoked_at.is_(None),
            )
            .values(consumed_at=consumed_at)
        )
        return bool(result.rowcount)

    async def revoke_token_family(
        self,
        family_id: UUID,
        *,
        revoked_at: datetime,
    ) -> int:
        result = await self.session.execute(
            update(AuthToken)
            .where(
                AuthToken.family_id == family_id,
                AuthToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        return int(result.rowcount or 0)

    async def record_login_attempt(
        self,
        attempt: LoginAttempt,
    ) -> None:
        self.session.add(attempt)

    async def failed_attempt_count(
        self,
        identifier: str,
        *,
        since: datetime,
    ) -> int:
        result = await self.session.execute(
            select(func.count(LoginAttempt.id)).where(
                LoginAttempt.normalized_identifier
                == identifier,
                LoginAttempt.succeeded.is_(False),
                LoginAttempt.attempted_at >= since,
            )
        )
        return int(result.scalar_one())

    async def get_security_state(
        self,
        user_id: UUID,
    ) -> AccountSecurityState | None:
        return await self.session.get(
            AccountSecurityState,
            user_id,
        )

    async def upsert_security_state(
        self,
        state: AccountSecurityState,
    ) -> AccountSecurityState:
        existing = await self.get_security_state(
            state.user_id
        )

        if existing is None:
            self.session.add(state)
            await self.session.flush()
            return state

        existing.failed_login_count = (
            state.failed_login_count
        )
        existing.locked_until = state.locked_until
        existing.email_verified_at = (
            state.email_verified_at
        )
        existing.password_changed_at = (
            state.password_changed_at
        )
        existing.security_version = (
            state.security_version
        )
        existing.updated_at = state.updated_at
        await self.session.flush()
        return existing

    async def add_password_history(
        self,
        history: PasswordHistory,
    ) -> None:
        self.session.add(history)

    async def recent_password_hashes(
        self,
        user_id: UUID,
        *,
        limit: int,
    ) -> list[str]:
        result = await self.session.execute(
            select(PasswordHistory.password_hash)
            .where(
                PasswordHistory.user_id == user_id
            )
            .order_by(
                PasswordHistory.created_at.desc()
            )
            .limit(limit)
        )
        return list(result.scalars())

    async def add_audit_event(
        self,
        event: AuthAuditEvent,
    ) -> None:
        self.session.add(event)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
