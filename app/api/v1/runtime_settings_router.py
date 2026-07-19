from fastapi import APIRouter, Depends

from app.core.runtime_settings import runtime_settings_status
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(prefix="/runtime-settings", tags=["runtime-settings"])


@router.get("/status")
async def get_runtime_settings_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return runtime_settings_status()
