from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.observability import observability_state
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.observability.metrics_service import (
    ObservabilityMetricsService,
)

router = APIRouter(
    prefix="/observability",
    tags=["observability"],
)


class ObservabilitySnapshotRequest(BaseModel):
    providers: list[str] = Field(
        default_factory=lambda: ["mock", "openai", "local"]
    )
    include_external_boundaries: bool = True
    preferred_provider: str = "mock"
    fallback_providers: list[str] = Field(default_factory=list)
    prompt_version: str = "shopping_v1"
    audit_persistence_mode: str = "in_memory_or_db_endpoint"


class StructuredLogRequest(BaseModel):
    level: str = "INFO"
    event: str
    message: str
    correlation_id: str | None = None
    trace_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class AuditEventRequest(BaseModel):
    event_type: str
    actor: str
    resource: str
    action: str
    outcome: str
    correlation_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


@router.get("/snapshot")
async def get_observability_snapshot(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return ObservabilityMetricsService().snapshot({})


@router.post("/snapshot")
async def create_observability_snapshot(
    payload: ObservabilitySnapshotRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return ObservabilityMetricsService().snapshot(
        payload.model_dump()
    )


@router.post("/clear")
def clear_observability_state(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    observability_state.clear()
    return {
        "cleared": True,
        "metadata": {
            "observability_version": "observability_v1"
        },
    }


@router.get("/traces/{trace_id}")
def get_trace(
    trace_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    trace = observability_state.get_trace(trace_id)

    if trace is None:
        raise HTTPException(
            status_code=404,
            detail="TRACE_NOT_FOUND",
        )

    return {
        "trace": trace,
        "metadata": {
            "tracing_version": "distributed_tracing_v1"
        },
    }


@router.post("/logs")
def create_structured_log(
    payload: StructuredLogRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    log = observability_state.add_log(
        level=payload.level,
        event=payload.event,
        message=payload.message,
        correlation_id=payload.correlation_id,
        trace_id=payload.trace_id,
        context=payload.context,
    )

    return {
        "recorded": True,
        "log": log,
        "metadata": {
            "logging_version": "structured_logging_v1"
        },
    }


@router.get("/logs")
def list_structured_logs(
    correlation_id: str | None = None,
    trace_id: str | None = None,
    level: str | None = None,
    limit: int = 100,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    logs = observability_state.list_logs(
        correlation_id=correlation_id,
        trace_id=trace_id,
        level=level,
        limit=limit,
    )

    return {
        "log_count": len(logs),
        "logs": logs,
        "metadata": {
            "logging_version": "structured_logging_v1"
        },
    }


@router.get("/timelines/{correlation_id}")
def get_request_timeline(
    correlation_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    events = observability_state.get_timeline(
        correlation_id
    )

    return {
        "correlation_id": correlation_id,
        "event_count": len(events),
        "events": events,
        "metadata": {
            "timeline_version": "request_timeline_v1"
        },
    }


@router.post("/audit-events")
def create_audit_event(
    payload: AuditEventRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    event = observability_state.add_audit_event(
        event_type=payload.event_type,
        actor=payload.actor,
        resource=payload.resource,
        action=payload.action,
        outcome=payload.outcome,
        correlation_id=payload.correlation_id,
        details=payload.details,
    )

    return {
        "recorded": True,
        "event": event,
        "metadata": {
            "audit_stream_version": "audit_event_stream_v1"
        },
    }


@router.get("/audit-events")
def list_audit_events(
    event_type: str | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
    limit: int = 100,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    events = observability_state.list_audit_events(
        event_type=event_type,
        actor=actor,
        correlation_id=correlation_id,
        limit=limit,
    )

    return {
        "event_count": len(events),
        "events": events,
        "metadata": {
            "audit_stream_version": "audit_event_stream_v1"
        },
    }