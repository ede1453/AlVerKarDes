from fastapi import APIRouter
from pydantic import BaseModel

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

router = APIRouter(prefix="/notification-outbox", tags=["notification-outbox"])

_service = NotificationOutboxService()


@router.post("/enqueue")
def enqueue_notification(payload: dict):
    return _service.enqueue(payload)


@router.post("/enqueue-many")
def enqueue_many_notifications(payload: dict):
    return _service.enqueue_many(payload.get("items", []))


@router.get("/pending")
def list_pending_notifications(limit: int = 50):
    return _service.list_pending(limit=limit)

@router.get("/readiness/status")
def get_production_readiness_status():
    return _service.get_production_readiness()


@router.post("/readiness/checks")
def update_production_readiness_check(
    payload: ReadinessCheckRequest,
):
    return _service.set_readiness_check(
        check_name=payload.check_name,
        passed=payload.passed,
        details=payload.details,
    )

@router.get("/release-manifest")
def get_release_manifest():
    return _service.get_release_manifest()


@router.post("/release-manifest/publish")
def publish_release_manifest(
    payload: ReleaseManifestRequest,
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
):
    return _service.get_release_audit_trail(
        event_type=event_type,
        limit=limit,
    )

@router.get("/release-approval/status")
def get_release_approval_status():
    return _service.get_release_approval_status()

@router.post("/release-approval/approve")
def approve_release(payload: ReleaseApprovalRequest):
    return _service.approve_release(
        approved_by=payload.approved_by,
        notes=payload.notes,
    )

@router.post("/release-approval/revoke")
def revoke_release_approval(payload: ReleaseApprovalRevokeRequest):
    return _service.revoke_release_approval(
        revoked_by=payload.revoked_by,
        reason=payload.reason,
    )

@router.post("/release-audit/events")
def record_release_audit_event(
    payload: ReleaseAuditEventRequest,
):
    return _service.record_release_audit_event(
        event_type=payload.event_type,
        actor=payload.actor,
        details=payload.details,
    )

@router.post("/claim-next")
def claim_next_notification():
    return _service.claim_next()

@router.get("/dead-letters")
def list_dead_letter_notifications(limit: int = 50):
    return _service.list_dead_letters(limit=limit)

@router.get("/metrics")
def get_notification_outbox_metrics():
    return _service.get_metrics()

@router.get("/channel-health")
def get_notification_channel_health():
    return _service.get_channel_health()

@router.get("/circuit-breaker/status")
def get_notification_circuit_breaker_status(failure_threshold: int = 3):
    return _service.get_circuit_breaker_status(
        failure_threshold=failure_threshold
    )

@router.get("/circuit-breaker/can-deliver")
def can_deliver_notification_with_circuit_breaker(
    failure_threshold: int = 3,
):
    return _service.can_deliver_notifications(
        failure_threshold=failure_threshold
    )

@router.get("/digest/{user_id}")
def get_notification_digest(user_id: str, limit: int = 20):
    return _service.build_digest_summary(
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
):
    return _service.check_quiet_hours(
        user_id=user_id,
        current_hour=current_hour,
        start_hour=start_hour,
        end_hour=end_hour,
        enabled=enabled,
    )

@router.get("/scheduler/status")
def get_background_scheduler_status():
    return _service.get_scheduler_status()

@router.post("/scheduler/jobs")
def register_background_scheduler_job(
    payload: ScheduledJobRequest,
):
    return _service.register_scheduled_job(
        job_name=payload.job_name,
        interval_seconds=payload.interval_seconds,
        enabled=payload.enabled,
    )

@router.post("/scheduler/jobs/{job_name}/run")
def run_background_scheduler_job(job_name: str):
    return _service.run_scheduled_job(
        job_name=job_name
    )

@router.get("/workers/status")
def get_distributed_worker_status():
    return _service.get_worker_status()


@router.post("/workers")
def register_distributed_worker(
    payload: WorkerRegistrationRequest,
):
    return _service.register_worker(
        worker_id=payload.worker_id,
        capacity=payload.capacity,
        enabled=payload.enabled,
    )


@router.post("/workers/assign")
def assign_distributed_worker_job(
    payload: WorkerAssignmentRequest,
):
    return _service.assign_job_to_worker(
        job_id=payload.job_id
    )


@router.post("/workers/{worker_id}/complete")
def complete_distributed_worker_job(
    worker_id: str,
    payload: WorkerCompletionRequest,
):
    return _service.complete_worker_job(
        worker_id=worker_id,
        job_id=payload.job_id,
    )

@router.get("/leader/status")
def get_notification_leader_status():
    return _service.get_leader_status()


@router.post("/leader/acquire")
def acquire_notification_leadership(
    payload: LeadershipLeaseRequest,
):
    return _service.acquire_leadership(
        worker_id=payload.worker_id,
        lease_seconds=payload.lease_seconds,
    )


@router.post("/leader/renew")
def renew_notification_leadership(
    payload: LeadershipLeaseRequest,
):
    return _service.renew_leadership(
        worker_id=payload.worker_id,
        lease_seconds=payload.lease_seconds,
    )


@router.post("/leader/release")
def release_notification_leadership(
    payload: LeadershipReleaseRequest,
):
    return _service.release_leadership(
        worker_id=payload.worker_id
    )

@router.get("/scaling/instances/status")
def get_horizontal_scaling_status():
    return _service.get_instance_status()


@router.post("/scaling/instances")
def register_horizontal_scaling_instance(
    payload: ScalingInstanceRequest,
):
    return _service.register_instance(
        instance_id=payload.instance_id,
        capacity=payload.capacity,
        healthy=payload.healthy,
    )


@router.post("/scaling/assign")
def assign_horizontal_scaling_request(
    payload: ScalingAssignmentRequest,
):
    return _service.assign_instance_load(
        request_id=payload.request_id
    )

@router.get("/release-rollback/status")
def get_release_rollback_status():
    return _service.get_release_rollback_status()


@router.post("/release-rollback/request")
def request_release_rollback(
    payload: ReleaseRollbackRequest,
):
    return _service.request_release_rollback(
        requested_by=payload.requested_by,
        reason=payload.reason,
    )

@router.get("/release-promotion/status")
def get_release_promotion_status():
    return _service.get_release_promotion_status()


@router.post("/release-promotion/promote")
def promote_release(
    payload: ReleasePromotionRequest,
):
    return _service.promote_release(
        environment=payload.environment,
        promoted_by=payload.promoted_by,
    )

@router.post("/release-rollback/complete")
def complete_release_rollback(
    payload: ReleaseRollbackCompleteRequest,
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
):
    return _service.release_instance_load(
        instance_id=instance_id,
        request_id=payload.request_id,
    )

@router.post("/dead-letters/{item_id}/replay")
def replay_dead_letter_notification(item_id: str, payload: dict | None = None):
    payload = payload or {}
    return _service.replay_dead_letter(
        item_id=item_id,
        replay_reason=payload.get("replay_reason", "manual_replay"),
        replayed_by=payload.get("replayed_by", "system"),
    )

@router.post("/{item_id}/mark-delivered")
def mark_notification_delivered(item_id: str):
    return _service.mark_delivered(item_id)


@router.post("/{item_id}/mark-failed")
def mark_notification_failed(item_id: str, payload: dict):
    return _service.mark_failed(
        item_id=item_id,
        error=payload.get("error", "UNKNOWN_ERROR"),
        next_retry_at=payload.get("next_retry_at"),
    )

@router.post("/clear")
def clear_notification_outbox():
    _service.repository.clear()
    return {"cleared": True, "metadata": {"outbox_version": "notification_outbox_v1"}}

@router.post("/requeue-due-retries")
def requeue_due_notification_retries(limit: int = 50):
    return _service.requeue_due_retries(limit=limit)

@router.get("/rate-limit/{user_id}")
def get_rate_limit(user_id:str, limit:int=5):
    return _service.check_rate_limit(user_id,limit)

@router.get("/tenant-quota/{tenant_id}")
def tenant_quota(tenant_id:str, limit:int=100):
    return _service.check_tenant_quota(tenant_id, limit)

@router.get("/priority-queue/{priority}")
def priority_queue(priority:str):
    return _service.get_priority_queue(priority)

@router.post("/batch-summary")
def batch_summary(payload: BatchSummaryRequest):
    return _service.batch_delivery_summary(
        payload.notification_ids
    )

@router.post("/template-preview")
def template_preview(payload: dict):
    return _service.notification_template_preview(
        payload["template"],
        payload.get("variables", {}),
    )

@router.get("/preferences/{user_id}")
def notification_preferences(user_id: str):
    return _service.get_user_notification_preferences(user_id)

@router.post("/snooze")
def snooze_notification(payload: dict):
    return _service.snooze_notification(
        payload["notification_id"],
        payload["until"]
    )

@router.post("/mute-channel")
def mute_channel(payload: dict):
    return _service.mute_notification_channel(
        payload["user_id"],
        payload["channel"],
    )

