from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.internal_service_auth import require_internal_service_key
from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.notifications.outbox.outbox_repository import (
    DEFAULT_STALE_LOCK_SECONDS,
    NotificationOutboxDBRepository,
)
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


class ScheduledJobRequest(BaseModel):
    job_name: str
    interval_seconds: int
    enabled: bool = True

class ReleasePromotionRequest(BaseModel):
    environment: str
    promoted_by: str
    
class ReleaseManifestRequest(BaseModel):
    release_version: str
    commit_sha: str
    build_id: str

class ReleaseAuditEventRequest(BaseModel):
    event_type: str
    actor: str
    details: dict = {}

class ReleaseApprovalRequest(BaseModel):
    approved_by: str
    notes: str = ""

class ReleaseApprovalRevokeRequest(BaseModel):
    revoked_by: str
    reason: str

class ReleaseRollbackRequest(BaseModel):
    requested_by: str
    reason: str

class ReleaseRollbackCompleteRequest(BaseModel):
    completed_by: str

class WorkerRegistrationRequest(BaseModel):
    worker_id: str
    capacity: int = 1
    enabled: bool = True

class LeadershipLeaseRequest(BaseModel):
    worker_id: str
    lease_seconds: int = 30

class ScalingInstanceRequest(BaseModel):
    instance_id: str
    capacity: int = 1
    healthy: bool = True

class ReadinessCheckRequest(BaseModel):
    check_name: str
    passed: bool
    details: str = ""

class ScalingAssignmentRequest(BaseModel):
    request_id: str


class ScalingReleaseRequest(BaseModel):
    request_id: str

class LeadershipReleaseRequest(BaseModel):
    worker_id: str

class WorkerAssignmentRequest(BaseModel):
    job_id: str


class WorkerCompletionRequest(BaseModel):
    job_id: str

class BatchSummaryRequest(BaseModel):
    notification_ids:list[str]

class NotificationClaimRequest(BaseModel):
    worker_id: str
    stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS

router = APIRouter(prefix="/notification-outbox", tags=["notification-outbox"])

# SCALE-007 Part 1: the message queue itself (enqueue/claim-next/mark-
# delivered/mark-failed/metrics/etc.) is now Postgres-backed and needs a
# per-request AsyncSession -- same reasoning as job_queue_router.py's
# _service(db) helper (SCALE-003). The module-level singleton below is kept
# for every OTHER concern this god-service still owns in-memory (release
# lifecycle, worker/instance/scheduler coordination, leader-election
# delegate, rate-limit/tenant-quota) -- out of scope for this change, see
# WIKI ADR-017/SCALE-005 for the full inventory.
_service = NotificationOutboxService()


def _queue_service(db: AsyncSession) -> NotificationOutboxService:
    return NotificationOutboxService(repository=NotificationOutboxDBRepository(db))


@router.post("/enqueue")
async def enqueue_notification(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).enqueue(payload)


@router.post("/enqueue-many")
async def enqueue_many_notifications(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).enqueue_many(payload.get("items", []))


@router.get("/pending")
async def list_pending_notifications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _queue_service(db).list_pending(limit=limit)

@router.get("/readiness/status")
def get_production_readiness_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_production_readiness()


@router.post("/readiness/checks")
def update_production_readiness_check(
    payload: ReadinessCheckRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.set_readiness_check(
        check_name=payload.check_name,
        passed=payload.passed,
        details=payload.details,
    )

@router.get("/release-manifest")
def get_release_manifest(
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.get_release_manifest()


@router.post("/release-manifest/publish")
def publish_release_manifest(
    payload: ReleaseManifestRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.publish_release_manifest(
        release_version=payload.release_version,
        commit_sha=payload.commit_sha,
        build_id=payload.build_id,
    )

@router.get("/release-audit/events")
def get_release_audit_events(
    event_type: str | None = None,
    limit: int = 100,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.get_release_audit_trail(
        event_type=event_type,
        limit=limit,
    )

@router.get("/release-approval/status")
def get_release_approval_status(
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.get_release_approval_status()

@router.post("/release-approval/approve")
def approve_release(
    payload: ReleaseApprovalRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.approve_release(
        approved_by=payload.approved_by,
        notes=payload.notes,
    )

@router.post("/release-approval/revoke")
def revoke_release_approval(
    payload: ReleaseApprovalRevokeRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.revoke_release_approval(
        revoked_by=payload.revoked_by,
        reason=payload.reason,
    )

@router.post("/release-audit/events")
def record_release_audit_event(
    payload: ReleaseAuditEventRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.record_release_audit_event(
        event_type=payload.event_type,
        actor=payload.actor,
        details=payload.details,
    )

@router.post("/claim-next")
async def claim_next_notification(
    payload: NotificationClaimRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).claim_next(
        worker_id=payload.worker_id,
        stale_lock_seconds=payload.stale_lock_seconds,
    )

@router.get("/dead-letters")
async def list_dead_letter_notifications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _queue_service(db).list_dead_letters(limit=limit)

@router.get("/metrics")
async def get_notification_outbox_metrics(
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _queue_service(db).get_metrics()

@router.get("/channel-health")
async def get_notification_channel_health(
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _queue_service(db).get_channel_health()

@router.get("/circuit-breaker/status")
async def get_notification_circuit_breaker_status(
    failure_threshold: int = 3,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _queue_service(db).get_circuit_breaker_status(
        failure_threshold=failure_threshold
    )

@router.get("/circuit-breaker/can-deliver")
async def can_deliver_notification_with_circuit_breaker(
    failure_threshold: int = 3,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).can_deliver_notifications(
        failure_threshold=failure_threshold
    )

@router.get("/digest/{user_id}")
async def get_notification_digest(
    user_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return await _queue_service(db).build_digest_summary(
        user_id=user_id,
        limit=limit,
    )


@router.get("/quiet-hours/{user_id}")
def check_notification_quiet_hours(
    user_id: str,
    current_hour: int,
    start_hour: int = 22,
    end_hour: int = 8,
    enabled: bool = True,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return _service.check_quiet_hours(
        user_id=user_id,
        current_hour=current_hour,
        start_hour=start_hour,
        end_hour=end_hour,
        enabled=enabled,
    )

@router.get("/scheduler/status")
def get_background_scheduler_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_scheduler_status()

@router.post("/scheduler/jobs")
def register_background_scheduler_job(
    payload: ScheduledJobRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_scheduled_job(
        job_name=payload.job_name,
        interval_seconds=payload.interval_seconds,
        enabled=payload.enabled,
    )

@router.post("/scheduler/jobs/{job_name}/run")
def run_background_scheduler_job(
    job_name: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.run_scheduled_job(
        job_name=job_name
    )

@router.get("/workers/status")
def get_distributed_worker_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_worker_status()


@router.post("/workers")
def register_distributed_worker(
    payload: WorkerRegistrationRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.register_worker(
        worker_id=payload.worker_id,
        capacity=payload.capacity,
        enabled=payload.enabled,
    )


@router.post("/workers/assign")
def assign_distributed_worker_job(
    payload: WorkerAssignmentRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.assign_job_to_worker(
        job_id=payload.job_id
    )


@router.post("/workers/{worker_id}/complete")
def complete_distributed_worker_job(
    worker_id: str,
    payload: WorkerCompletionRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.complete_worker_job(
        worker_id=worker_id,
        job_id=payload.job_id,
    )

@router.get("/leader/status")
def get_notification_leader_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_leader_status()


@router.post("/leader/acquire")
def acquire_notification_leadership(
    payload: LeadershipLeaseRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.acquire_leadership(
        worker_id=payload.worker_id,
        lease_seconds=payload.lease_seconds,
    )


@router.post("/leader/renew")
def renew_notification_leadership(
    payload: LeadershipLeaseRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.renew_leadership(
        worker_id=payload.worker_id,
        lease_seconds=payload.lease_seconds,
    )


@router.post("/leader/release")
def release_notification_leadership(
    payload: LeadershipReleaseRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.release_leadership(
        worker_id=payload.worker_id
    )

@router.get("/scaling/instances/status")
def get_horizontal_scaling_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_instance_status()


@router.post("/scaling/instances")
def register_horizontal_scaling_instance(
    payload: ScalingInstanceRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.register_instance(
        instance_id=payload.instance_id,
        capacity=payload.capacity,
        healthy=payload.healthy,
    )


@router.post("/scaling/assign")
def assign_horizontal_scaling_request(
    payload: ScalingAssignmentRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.assign_instance_load(
        request_id=payload.request_id
    )

@router.get("/release-rollback/status")
def get_release_rollback_status(
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.get_release_rollback_status()


@router.post("/release-rollback/request")
def request_release_rollback(
    payload: ReleaseRollbackRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.request_release_rollback(
        requested_by=payload.requested_by,
        reason=payload.reason,
    )

@router.get("/release-promotion/status")
def get_release_promotion_status(
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.get_release_promotion_status()


@router.post("/release-promotion/promote")
def promote_release(
    payload: ReleasePromotionRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.promote_release(
        environment=payload.environment,
        promoted_by=payload.promoted_by,
    )

@router.post("/release-rollback/complete")
def complete_release_rollback(
    payload: ReleaseRollbackCompleteRequest,
    # AUTH-006 Parça 3 (ADR-005): RELEASE_MANAGER+ gerektirir (release lifecycle).
    current_user=Depends(require_role(UserRole.RELEASE_MANAGER)),
):
    return _service.complete_release_rollback(
        completed_by=payload.completed_by
    )

@router.post(
    "/scaling/instances/{instance_id}/release"
)
def release_horizontal_scaling_request(
    instance_id: str,
    payload: ScalingReleaseRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.release_instance_load(
        instance_id=instance_id,
        request_id=payload.request_id,
    )

@router.post("/dead-letters/{item_id}/replay")
async def replay_dead_letter_notification(
    item_id: str,
    payload: dict | None = None,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    payload = payload or {}
    return await _queue_service(db).replay_dead_letter(
        item_id=item_id,
        replay_reason=payload.get("replay_reason", "manual_replay"),
        replayed_by=payload.get("replayed_by", "system"),
    )

@router.post("/{item_id}/mark-delivered")
async def mark_notification_delivered(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).mark_delivered(item_id)


@router.post("/{item_id}/mark-failed")
async def mark_notification_failed(
    item_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).mark_failed(
        item_id=item_id,
        error=payload.get("error", "UNKNOWN_ERROR"),
        next_retry_at=payload.get("next_retry_at"),
    )

@router.post("/clear")
async def clear_notification_outbox(
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    await NotificationOutboxDBRepository(db).clear()
    return {"cleared": True, "metadata": {"outbox_version": "notification_outbox_v1"}}

@router.post("/requeue-due-retries")
async def requeue_due_notification_retries(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _queue_service(db).requeue_due_retries(limit=limit)

@router.get("/rate-limit/{user_id}")
def get_rate_limit(
    user_id: str,
    limit: int = 5,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return _service.check_rate_limit(user_id,limit)

@router.get("/tenant-quota/{tenant_id}")
def tenant_quota(
    tenant_id: str,
    limit: int = 100,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.check_tenant_quota(tenant_id, limit)

@router.get("/priority-queue/{priority}")
def priority_queue(
    priority: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_priority_queue(priority)

@router.post("/batch-summary")
def batch_summary(
    payload: BatchSummaryRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.batch_delivery_summary(
        payload.notification_ids
    )

@router.post("/template-preview")
def template_preview(
    payload: dict,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.notification_template_preview(
        payload["template"],
        payload.get("variables", {}),
    )

@router.get("/preferences/{user_id}")
def notification_preferences(
    user_id: str,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return _service.get_user_notification_preferences(user_id)

@router.post("/snooze")
async def snooze_notification(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # AUTH-006 Parça 2 bug fix: snooze_notification() önceden var olan
    # repository lookup'ını hiç kullanmayan bir stub'du (hep "SNOOZED"
    # dönerdi, sahiplik kontrolü mümkün değildi). Artık gerçek kaydı önce
    # buradan çekip sahiplik kontrolü yapıyoruz, tıpkı deal-notifications'ın
    # {id}/delivered ucundaki gibi (bkz. ADR-005).
    queue_service = _queue_service(db)
    notification_id = payload["notification_id"]
    item = await queue_service.get_notification(notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="notification_not_found")
    ensure_owner(current_user, item.user_id)
    return await queue_service.snooze_notification(
        notification_id,
        payload["until"]
    )

@router.post("/mute-channel")
def mute_channel(
    payload: dict,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload["user_id"])
    return _service.mute_notification_channel(
        payload["user_id"],
        payload["channel"],
    )

