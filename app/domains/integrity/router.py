from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.integrity.data_integrity_guard import DataIntegrityGuard
from app.domains.integrity.data_integrity_repository import DataIntegrityRepository

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.get("/check")
async def check_integrity(db: AsyncSession = Depends(get_db)):
    report = await DataIntegrityGuard().run(DataIntegrityRepository(db))
    return {
        "passed": report.passed,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "count": check.count,
                "message": check.message,
            }
            for check in report.checks
        ],
        "failed_checks": [
            {
                "name": check.name,
                "count": check.count,
                "message": check.message,
            }
            for check in report.failed_checks
        ],
    }
