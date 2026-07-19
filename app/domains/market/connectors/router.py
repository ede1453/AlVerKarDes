from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.market.connectors.import_service import FeedImportService
from app.domains.market.connectors.registry import create_default_feed_registry

router = APIRouter(prefix="/connectors")


@router.post("/import")
async def import_feed(
    connector_name: str,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    service = FeedImportService(db, create_default_feed_registry())
    result = await service.import_feed(connector_name=connector_name, path=Path(file_path))
    return result.model_dump()
