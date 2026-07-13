from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domains.integrity.data_integrity_guard import DataIntegrityGuard
from app.domains.integrity.data_integrity_repository import DataIntegrityRepository
from app.domains.integrity.duplicate_product_regression import DuplicateProductRegressionGuard
from app.domains.integrity.duplicate_product_regression_repository import DuplicateProductRegressionRepository
from app.domains.notifications.health import NotificationQueueHealthService
from app.domains.notifications.repository import PendingNotificationRepository
from app.domains.products.intelligence.merge_candidate_health import MergeCandidateHealthService
from app.domains.products.intelligence.merge_candidate_repository import MergeCandidateRepository
from app.domains.system.release_health import ReleaseHealthService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/release-health")
async def release_health(db: AsyncSession = Depends(get_db)):
    report = await ReleaseHealthService().run(
        integrity_guard=DataIntegrityGuard(),
        integrity_repo=DataIntegrityRepository(db),
        duplicate_regression_guard=DuplicateProductRegressionGuard(),
        duplicate_regression_repo=DuplicateProductRegressionRepository(db),
        notification_health_service=NotificationQueueHealthService(
            PendingNotificationRepository(db)
        ),
        merge_candidate_health_service=MergeCandidateHealthService(
            MergeCandidateRepository(db)
        ),
        metadata={
            "service": "AI Consumer Intelligence",
            "environment": getattr(settings, "app_env", "production"),
        },
    )

    return {
        "status": report.status,
        "passed": report.passed,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "data": check.data,
                "error": check.error,
            }
            for check in report.checks
        ],
        "failed_checks": [
            {
                "name": check.name,
                "error": check.error,
                "data": check.data,
            }
            for check in report.failed_checks
        ],
    }
