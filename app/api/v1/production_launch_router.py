from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.production_launch.service import (
    ProductionLaunchService,
)

router = APIRouter(
    prefix="/production-launch",
    tags=["production-launch"],
)

_service = ProductionLaunchService()


class PayloadRequest(BaseModel):
    payload: dict[str, Any] = Field(
        default_factory=dict
    )


_METHODS = {
    "database-config": "check_database_configuration",
    "transaction-boundary": "validate_transaction_boundary",
    "restart-marker-create": "create_restart_marker",
    "restart-marker-verify": "verify_restart_marker",
    "connection-pool": "evaluate_connection_pool",
    "migration-state": "validate_migration_state",
    "idempotent-write": "validate_idempotent_write",
    "data-retention": "evaluate_data_retention",
    "integrity-hash": "calculate_integrity_hash",
    "read-replica": "evaluate_read_replica",
    "persistence-readiness": "build_persistence_readiness",
    "connector-check": "register_connector_check",
    "connector-credentials": "validate_connector_credentials",
    "secret-reference": "register_secret_reference",
    "secret-leak": "detect_secret_leak",
    "connector-retry": "evaluate_connector_retry",
    "connector-circuit": "evaluate_connector_circuit",
    "connector-rate-limit": "evaluate_connector_rate_limit",
    "connector-readiness": "build_connector_readiness",
    "rate-limit": "evaluate_rate_limit",
    "cors": "validate_cors",
    "security-headers": "build_security_headers",
    "password-policy": "validate_password_policy",
    "security-readiness": "build_security_readiness",
    "deployment-register": "register_deployment",
    "container-image": "evaluate_container_image",
    "tls": "evaluate_tls",
    "health-endpoints": "evaluate_health_endpoints",
    "rollback-plan": "create_rollback_plan",
    "deployment-readiness": "build_deployment_readiness",
    "backup-register": "register_backup",
    "backup-verify": "verify_backup",
    "restore-drill": "record_restore_drill",
    "disaster-recovery": "evaluate_disaster_recovery",
    "backup-readiness": "build_backup_readiness",
    "smoke-test": "record_smoke_test",
    "load-test": "evaluate_load_test",
    "release-check": "register_release_check",
    "go-no-go": "evaluate_go_no_go",
    "release-manifest": "build_release_manifest",
}


@router.post("/clear")
def clear_state(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    global _service
    _service = ProductionLaunchService()
    return {"cleared": True}


@router.post("/{operation}")
def execute_operation(
    operation: str,
    payload: PayloadRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    method_name = _METHODS.get(operation)

    if method_name is None:
        return {
            "executed": False,
            "reason": "UNKNOWN_OPERATION",
        }

    method = getattr(_service, method_name)
    result = method(**payload.payload)

    return {
        "executed": True,
        "operation": operation,
        "result": result,
    }
