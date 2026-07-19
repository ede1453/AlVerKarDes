from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover - compatibility for older app layouts
    get_db = None

from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService


class LLMAuditTraceCreateRequest(BaseModel):
    request_payload: dict
    gateway_response: dict


router = APIRouter(prefix="/llm-audit-traces", tags=["llm-audit-traces"])

_in_memory_service = LLMAuditTraceService()


def _service_for_db(db=None):
    if db is None:
        return _in_memory_service

    return LLMAuditTraceService(db=db)


def _db_dependency():
    if get_db is None:
        return None

    return Depends(get_db)


@router.post("")
async def create_llm_audit_trace(
    payload: LLMAuditTraceCreateRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _in_memory_service.create_from_gateway_payload(
        request_payload=payload.request_payload,
        gateway_response=payload.gateway_response,
    )


@router.get("")
async def list_llm_audit_traces(
    limit: int = Query(default=20, ge=1, le=100),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return {
        "items": await _in_memory_service.list_recent(limit=limit),
        "limit": limit,
    }


@router.get("/{trace_id}")
async def get_llm_audit_trace(
    trace_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    result = await _in_memory_service.get(trace_id)
    if result is None:
        raise HTTPException(status_code=404, detail="llm_audit_trace_not_found")
    return result


if get_db is not None:
    @router.post("/db")
    async def create_llm_audit_trace_db(
        payload: LLMAuditTraceCreateRequest,
        db=Depends(get_db),
        # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
        current_user=Depends(require_role(UserRole.OPERATOR)),
    ):
        service = _service_for_db(db)
        return await service.create_from_gateway_payload(
            request_payload=payload.request_payload,
            gateway_response=payload.gateway_response,
        )


    @router.get("/db/list")
    async def list_llm_audit_traces_db(
        limit: int = Query(default=20, ge=1, le=100),
        db=Depends(get_db),
        # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
        current_user=Depends(require_role(UserRole.OPERATOR)),
    ):
        service = _service_for_db(db)
        return {
            "items": await service.list_recent(limit=limit),
            "limit": limit,
        }


    @router.get("/db/{trace_id}")
    async def get_llm_audit_trace_db(
        trace_id: str,
        db=Depends(get_db),
        # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
        current_user=Depends(require_role(UserRole.OPERATOR)),
    ):
        service = _service_for_db(db)
        result = await service.get(trace_id)
        if result is None:
            raise HTTPException(status_code=404, detail="llm_audit_trace_not_found")
        return result
