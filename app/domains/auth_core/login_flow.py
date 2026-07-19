from __future__ import annotations

from app.domains.auth_core.service import (
    AuthenticationCoreError,
    AuthenticationCoreService,
)
from app.domains.auth_core.types import AuthContext, TokenPair
from app.domains.identity.repository import UserRepository


async def authenticate_and_issue_tokens(
    *,
    identifier: str,
    password: str,
    context: AuthContext,
    user_repository: UserRepository,
    auth_service: AuthenticationCoreService,
) -> TokenPair:
    """Single credential-check + lockout + token-issuance path.

    Used by both /auth/login (auth_core) and /identity/login so there is
    exactly one login implementation and one place account lockout is
    enforced, instead of the two independent, unprotected paths that
    existed before (see ADR-002 durum güncellemesi, 2026-07-18).
    """
    user = await user_repository.get_by_email(identifier)

    if user is not None:
        await auth_service.check_login_allowed(user_id=user.id)

    if (
        user is None
        or not user.password_hash
        or not auth_service.password_verifier(password, user.password_hash)
    ):
        await auth_service.record_failed_login(
            identifier=identifier,
            user_id=user.id if user is not None else None,
            context=context,
            reason="INVALID_CREDENTIALS",
        )
        raise AuthenticationCoreError("INVALID_CREDENTIALS", status_code=401)

    await auth_service.record_successful_login(
        identifier=identifier,
        user_id=user.id,
        context=context,
    )
    return await auth_service.issue_token_pair(user_id=user.id, context=context)
