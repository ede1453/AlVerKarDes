from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import compare_digest
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from app.domains.auth_core.models import (
    AccountSecurityState,
    AuthAuditEvent,
    AuthSession,
    AuthToken,
    LoginAttempt,
    PasswordHistory,
)
from app.domains.auth_core.password_policy import (
    PasswordPolicy,
)
from app.domains.auth_core.repository import (
    AuthenticationCoreRepository,
)
from app.domains.auth_core.tokens import (
    TokenCodec,
    create_opaque_token,
    hash_opaque_token,
)
from app.domains.auth_core.types import (
    AuthContext,
    AuthEventType,
    AuthSessionStatus,
    AuthTokenPurpose,
    AuthenticationResult,
    TokenPair,
)


PasswordVerifier = Callable[
    [str, str],
    bool,
]
PasswordHasher = Callable[
    [str],
    str,
]


class AuthenticationCoreError(ValueError):
    def __init__(
        self,
        code: str,
        *,
        status_code: int = 400,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class AuthenticationCoreService:
    def __init__(
        self,
        repository: AuthenticationCoreRepository,
        *,
        token_codec: TokenCodec,
        password_policy: PasswordPolicy,
        password_verifier: PasswordVerifier,
        password_hasher: PasswordHasher,
        access_minutes: int = 30,
        refresh_days: int = 30,
        session_days: int = 90,
        maximum_failed_attempts: int = 5,
        lockout_minutes: int = 15,
        attempt_window_minutes: int = 15,
        password_history_limit: int = 5,
    ) -> None:
        self.repository = repository
        self.token_codec = token_codec
        self.password_policy = password_policy
        self.password_verifier = password_verifier
        self.password_hasher = password_hasher
        self.access_minutes = access_minutes
        self.refresh_days = refresh_days
        self.session_days = session_days
        self.maximum_failed_attempts = (
            maximum_failed_attempts
        )
        self.lockout_minutes = lockout_minutes
        self.attempt_window_minutes = (
            attempt_window_minutes
        )
        self.password_history_limit = (
            password_history_limit
        )

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    async def emit_event(
        self,
        *,
        event_type: AuthEventType,
        context: AuthContext,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        details: dict | None = None,
    ) -> None:
        await self.repository.add_audit_event(
            AuthAuditEvent(
                user_id=user_id,
                session_id=session_id,
                event_type=event_type.value,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                correlation_id=(
                    context.correlation_id
                ),
                details=details or {},
                occurred_at=self.now(),
            )
        )

    async def ensure_security_state(
        self,
        user_id: UUID,
    ) -> AccountSecurityState:
        state = (
            await self.repository.get_security_state(
                user_id
            )
        )

        if state is not None:
            return state

        now = self.now()
        return await self.repository.upsert_security_state(
            AccountSecurityState(
                user_id=user_id,
                failed_login_count=0,
                locked_until=None,
                email_verified_at=None,
                password_changed_at=None,
                security_version=1,
                updated_at=now,
            )
        )

    async def check_login_allowed(
        self,
        *,
        user_id: UUID,
    ) -> None:
        state = await self.ensure_security_state(
            user_id
        )
        now = self.now()

        if (
            state.locked_until is not None
            and state.locked_until > now
        ):
            raise AuthenticationCoreError(
                "ACCOUNT_TEMPORARILY_LOCKED",
                status_code=423,
            )

    async def record_failed_login(
        self,
        *,
        identifier: str,
        user_id: UUID | None,
        context: AuthContext,
        reason: str,
    ) -> None:
        now = self.now()
        normalized = identifier.strip().casefold()

        await self.repository.record_login_attempt(
            LoginAttempt(
                normalized_identifier=normalized,
                user_id=user_id,
                succeeded=False,
                ip_address=context.ip_address,
                attempted_at=now,
                failure_reason=reason,
            )
        )

        if user_id is not None:
            state = await self.ensure_security_state(
                user_id
            )
            state.failed_login_count += 1

            if (
                state.failed_login_count
                >= self.maximum_failed_attempts
            ):
                state.locked_until = (
                    now
                    + timedelta(
                        minutes=self.lockout_minutes
                    )
                )
                await self.emit_event(
                    event_type=(
                        AuthEventType.ACCOUNT_LOCKED
                    ),
                    context=context,
                    user_id=user_id,
                    details={
                        "locked_until": (
                            state.locked_until.isoformat()
                        )
                    },
                )

            state.updated_at = now
            await self.repository.upsert_security_state(
                state
            )

        await self.emit_event(
            event_type=AuthEventType.LOGIN_FAILED,
            context=context,
            user_id=user_id,
            details={"reason": reason},
        )
        await self.repository.commit()

    async def record_successful_login(
        self,
        *,
        identifier: str,
        user_id: UUID,
        context: AuthContext,
    ) -> None:
        now = self.now()
        state = await self.ensure_security_state(
            user_id
        )
        state.failed_login_count = 0
        state.locked_until = None
        state.updated_at = now

        await self.repository.upsert_security_state(
            state
        )
        await self.repository.record_login_attempt(
            LoginAttempt(
                normalized_identifier=(
                    identifier.strip().casefold()
                ),
                user_id=user_id,
                succeeded=True,
                ip_address=context.ip_address,
                attempted_at=now,
                failure_reason=None,
            )
        )
        await self.emit_event(
            event_type=AuthEventType.LOGIN_SUCCEEDED,
            context=context,
            user_id=user_id,
        )
        await self.repository.commit()

    async def issue_token_pair(
        self,
        *,
        user_id: UUID,
        context: AuthContext,
        session_id: UUID | None = None,
        refresh_family_id: UUID | None = None,
        parent_token_id: UUID | None = None,
    ) -> TokenPair:
        now = self.now()
        state = await self.ensure_security_state(
            user_id
        )

        if session_id is None:
            session = AuthSession(
                user_id=user_id,
                status=AuthSessionStatus.ACTIVE.value,
                device_name=context.device_name,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                created_at=now,
                last_seen_at=now,
                expires_at=(
                    now
                    + timedelta(
                        days=self.session_days
                    )
                ),
                revoked_at=None,
                revoke_reason=None,
            )
            await self.repository.create_session(
                session
            )
            session_id = session.id

            await self.emit_event(
                event_type=(
                    AuthEventType.SESSION_CREATED
                ),
                context=context,
                user_id=user_id,
                session_id=session_id,
            )

        refresh_token = create_opaque_token()
        refresh_expires_at = (
            now
            + timedelta(days=self.refresh_days)
        )
        family_id = (
            refresh_family_id or uuid4()
        )

        refresh_row = AuthToken(
            user_id=user_id,
            session_id=session_id,
            purpose=AuthTokenPurpose.REFRESH.value,
            token_hash=hash_opaque_token(
                refresh_token
            ),
            family_id=family_id,
            parent_token_id=parent_token_id,
            issued_at=now,
            expires_at=refresh_expires_at,
            consumed_at=None,
            revoked_at=None,
            metadata_json={
                "ip_address": context.ip_address,
                "user_agent": context.user_agent,
            },
        )
        await self.repository.create_token(
            refresh_row
        )

        access_token, access_expires_at = (
            self.token_codec.encode_access_token(
                user_id=str(user_id),
                session_id=str(session_id),
                security_version=(
                    state.security_version
                ),
            )
        )

        await self.repository.commit()

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            access_expires_at=(
                access_expires_at
            ),
            refresh_expires_at=(
                refresh_expires_at
            ),
            session_id=str(session_id),
        )

    async def rotate_refresh_token(
        self,
        *,
        raw_refresh_token: str,
        context: AuthContext,
    ) -> TokenPair:
        now = self.now()
        token_hash = hash_opaque_token(
            raw_refresh_token
        )
        token = (
            await self.repository.get_token_by_hash(
                token_hash
            )
        )

        if (
            token is None
            or token.purpose
            != AuthTokenPurpose.REFRESH.value
        ):
            raise AuthenticationCoreError(
                "REFRESH_TOKEN_INVALID",
                status_code=401,
            )

        if token.revoked_at is not None:
            raise AuthenticationCoreError(
                "REFRESH_TOKEN_REVOKED",
                status_code=401,
            )

        if token.expires_at <= now:
            raise AuthenticationCoreError(
                "REFRESH_TOKEN_EXPIRED",
                status_code=401,
            )

        if token.consumed_at is not None:
            await self.repository.revoke_token_family(
                token.family_id,
                revoked_at=now,
            )

            if token.session_id is not None:
                await self.repository.revoke_session(
                    token.session_id,
                    revoked_at=now,
                    reason=(
                        "refresh_token_reuse"
                    ),
                    status=(
                        AuthSessionStatus
                        .COMPROMISED
                        .value
                    ),
                )

            await self.emit_event(
                event_type=(
                    AuthEventType
                    .REFRESH_REUSE_DETECTED
                ),
                context=context,
                user_id=token.user_id,
                session_id=token.session_id,
                details={
                    "family_id": str(
                        token.family_id
                    )
                },
            )
            await self.repository.commit()

            raise AuthenticationCoreError(
                "REFRESH_TOKEN_REUSE_DETECTED",
                status_code=401,
            )

        session = (
            await self.repository.get_session(
                token.session_id
            )
        )

        if (
            session is None
            or session.status
            != AuthSessionStatus.ACTIVE.value
            or session.revoked_at is not None
            or session.expires_at <= now
        ):
            raise AuthenticationCoreError(
                "SESSION_INACTIVE",
                status_code=401,
            )

        consumed = (
            await self.repository.consume_token(
                token.id,
                consumed_at=now,
            )
        )

        if not consumed:
            raise AuthenticationCoreError(
                "REFRESH_TOKEN_CONCURRENT_USE",
                status_code=409,
            )

        pair = await self.issue_token_pair(
            user_id=token.user_id,
            context=context,
            session_id=token.session_id,
            refresh_family_id=token.family_id,
            parent_token_id=token.id,
        )

        session.last_seen_at = now

        await self.emit_event(
            event_type=(
                AuthEventType.REFRESH_ROTATED
            ),
            context=context,
            user_id=token.user_id,
            session_id=token.session_id,
        )
        await self.repository.commit()
        return pair

    async def revoke_session(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        context: AuthContext,
        reason: str = "user_logout",
    ) -> bool:
        session = (
            await self.repository.get_session(
                session_id
            )
        )

        if (
            session is None
            or session.user_id != user_id
        ):
            return False

        revoked = (
            await self.repository.revoke_session(
                session_id,
                revoked_at=self.now(),
                reason=reason,
            )
        )

        if revoked:
            await self.emit_event(
                event_type=(
                    AuthEventType.SESSION_REVOKED
                ),
                context=context,
                user_id=user_id,
                session_id=session_id,
                details={"reason": reason},
            )
            await self.repository.commit()

        return revoked

    async def revoke_all_sessions(
        self,
        *,
        user_id: UUID,
        context: AuthContext,
        except_session_id: UUID | None = None,
    ) -> int:
        count = (
            await self.repository.revoke_all_sessions(
                user_id,
                revoked_at=self.now(),
                reason="user_logout_all",
                except_session_id=(
                    except_session_id
                ),
            )
        )
        await self.emit_event(
            event_type=(
                AuthEventType.SESSION_REVOKED
            ),
            context=context,
            user_id=user_id,
            details={
                "all_sessions": True,
                "revoked_count": count,
            },
        )
        await self.repository.commit()
        return count

    async def issue_purpose_token(
        self,
        *,
        user_id: UUID,
        purpose: AuthTokenPurpose,
        context: AuthContext,
        lifetime_minutes: int,
    ) -> str:
        now = self.now()
        raw = create_opaque_token()

        await self.repository.create_token(
            AuthToken(
                user_id=user_id,
                session_id=None,
                purpose=purpose.value,
                token_hash=hash_opaque_token(
                    raw
                ),
                family_id=None,
                parent_token_id=None,
                issued_at=now,
                expires_at=(
                    now
                    + timedelta(
                        minutes=lifetime_minutes
                    )
                ),
                consumed_at=None,
                revoked_at=None,
                metadata_json={},
            )
        )

        event_type = (
            AuthEventType
            .EMAIL_VERIFICATION_ISSUED
            if purpose
            == AuthTokenPurpose
            .EMAIL_VERIFICATION
            else AuthEventType
            .PASSWORD_RESET_ISSUED
        )

        await self.emit_event(
            event_type=event_type,
            context=context,
            user_id=user_id,
        )
        await self.repository.commit()
        return raw

    async def consume_purpose_token(
        self,
        *,
        raw_token: str,
        purpose: AuthTokenPurpose,
    ) -> AuthToken:
        now = self.now()
        token = (
            await self.repository.get_token_by_hash(
                hash_opaque_token(raw_token)
            )
        )

        if token is None or token.purpose != purpose.value:
            raise AuthenticationCoreError(
                "TOKEN_INVALID",
                status_code=400,
            )

        if (
            token.revoked_at is not None
            or token.consumed_at is not None
        ):
            raise AuthenticationCoreError(
                "TOKEN_ALREADY_USED",
                status_code=400,
            )

        if token.expires_at <= now:
            raise AuthenticationCoreError(
                "TOKEN_EXPIRED",
                status_code=400,
            )

        consumed = (
            await self.repository.consume_token(
                token.id,
                consumed_at=now,
            )
        )

        if not consumed:
            raise AuthenticationCoreError(
                "TOKEN_CONCURRENT_USE",
                status_code=409,
            )

        return token

    async def confirm_email_verification(
        self,
        *,
        raw_token: str,
        context: AuthContext,
    ) -> UUID:
        token = await self.consume_purpose_token(
            raw_token=raw_token,
            purpose=(
                AuthTokenPurpose
                .EMAIL_VERIFICATION
            ),
        )
        state = await self.ensure_security_state(
            token.user_id
        )
        state.email_verified_at = self.now()
        state.updated_at = self.now()

        await self.repository.upsert_security_state(
            state
        )
        await self.emit_event(
            event_type=AuthEventType.EMAIL_VERIFIED,
            context=context,
            user_id=token.user_id,
        )
        await self.repository.commit()
        return token.user_id

    async def validate_new_password(
        self,
        *,
        user_id: UUID,
        new_password: str,
        identity_fragments: tuple[str, ...],
    ) -> str:
        policy = self.password_policy.evaluate(
            new_password,
            identity_fragments=identity_fragments,
        )

        if not policy.valid:
            raise AuthenticationCoreError(
                ",".join(policy.errors),
                status_code=422,
            )

        recent_hashes = (
            await self.repository
            .recent_password_hashes(
                user_id,
                limit=self.password_history_limit,
            )
        )

        for old_hash in recent_hashes:
            if self.password_verifier(
                new_password,
                old_hash,
            ):
                raise AuthenticationCoreError(
                    "PASSWORD_RECENTLY_USED",
                    status_code=422,
                )

        return self.password_hasher(
            new_password
        )

    async def complete_password_reset(
        self,
        *,
        raw_token: str,
        new_password: str,
        identity_fragments: tuple[str, ...],
        set_user_password_hash: Callable[
            [UUID, str],
            Awaitable[None],
        ],
        context: AuthContext,
    ) -> UUID:
        token = await self.consume_purpose_token(
            raw_token=raw_token,
            purpose=(
                AuthTokenPurpose.PASSWORD_RESET
            ),
        )
        new_hash = await self.validate_new_password(
            user_id=token.user_id,
            new_password=new_password,
            identity_fragments=(
                identity_fragments
            ),
        )

        await set_user_password_hash(
            token.user_id,
            new_hash,
        )
        await self.repository.add_password_history(
            PasswordHistory(
                user_id=token.user_id,
                password_hash=new_hash,
                created_at=self.now(),
            )
        )

        state = await self.ensure_security_state(
            token.user_id
        )
        state.password_changed_at = self.now()
        state.security_version += 1
        state.updated_at = self.now()
        await self.repository.upsert_security_state(
            state
        )

        await self.repository.revoke_all_sessions(
            token.user_id,
            revoked_at=self.now(),
            reason="password_reset",
        )
        await self.emit_event(
            event_type=(
                AuthEventType
                .PASSWORD_RESET_COMPLETED
            ),
            context=context,
            user_id=token.user_id,
        )
        await self.repository.commit()
        return token.user_id
