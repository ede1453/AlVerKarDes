from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.auth_core.dependencies import get_token_codec
from app.domains.auth_core.tokens import TokenCodec, TokenValidationError
from app.domains.identity.models import UserRole
from app.domains.identity.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    codec: TokenCodec = Depends(get_token_codec),
):
    # HTTPBearer's default auto_error raises 403 when the header is simply
    # missing, which collides with 403 meaning "authenticated but forbidden"
    # elsewhere in this API. auto_error=False + this explicit check makes a
    # missing token 401, same as an invalid one.
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "AUTHENTICATION_REQUIRED"})

    # Access tokens are issued exclusively by auth_core's login/refresh flow
    # (see login_flow.authenticate_and_issue_tokens), so they must be decoded
    # with the same TokenCodec/claim set rather than a bare jwt.decode.
    try:
        payload = codec.decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise TokenValidationError("ACCESS_TOKEN_SUBJECT_MISSING")
    except TokenValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_TOKEN"}) from exc

    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "USER_NOT_FOUND"})
    return user


def ensure_owner(current_user, resource_user_id) -> None:
    """Raise 403 if the resource's owner doesn't match the authenticated user.
    Compares as strings since resource_user_id may be a str or UUID."""
    if str(current_user.id) != str(resource_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_RESOURCE_OWNER"},
        )


# AUTH-006 Part 3 (ADR-005): roles are hierarchical, not a flat set --
# SUPERADMIN outranks RELEASE_MANAGER outranks OPERATOR outranks SHOPPER.
# require_role(X) means "X or anything above X", not "exactly X". This is
# what makes a RELEASE_MANAGER able to reach every OPERATOR-gated endpoint
# too, not just the release-lifecycle ones -- confirmed as the intended
# behavior before implementing (a RELEASE_MANAGER is a superset of OPERATOR
# here, not a disjoint role).
_ROLE_RANK = {
    UserRole.SHOPPER: 0,
    UserRole.OPERATOR: 1,
    UserRole.RELEASE_MANAGER: 2,
    UserRole.SUPERADMIN: 3,
}


def require_role(minimum_role: UserRole):
    """Dependency factory: the caller must hold at least `minimum_role`
    (see _ROLE_RANK for the hierarchy). Built on top of get_current_user, so
    a missing/invalid token still surfaces as 401 before the role check
    (which is 403) ever runs."""

    def dependency(current_user=Depends(get_current_user)):
        if _ROLE_RANK[current_user.role] < _ROLE_RANK[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "INSUFFICIENT_ROLE", "required_role": minimum_role.value},
            )
        return current_user

    return dependency