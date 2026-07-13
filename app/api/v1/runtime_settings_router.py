from fastapi import APIRouter

from app.core.runtime_settings import runtime_settings_status

router = APIRouter(prefix="/runtime-settings", tags=["runtime-settings"])


@router.get("/status")
async def get_runtime_settings_status():
    return runtime_settings_status()
