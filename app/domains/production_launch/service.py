from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class ProductionLaunchService:
    def __init__(self) -> None:
        self._restart_markers: dict[str, dict[str, Any]] = {}
        self._connector_checks: dict[str, dict[str, Any]] = {}
        self._secrets: dict[str, dict[str, Any]] = {}
        self._security_events: list[dict[str, Any]] = []
        self._deployments: dict[str, dict[str, Any]] = {}
        self._backups: dict[str, dict[str, Any]] = {}
        self._restore_drills: list[dict[str, Any]] = []
        self._smoke_runs: list[dict[str, Any]] = []
        self._load_runs: list[dict[str, Any]] = []
        self._release_checks: dict[str, dict[str, Any]] = {}

    # RC301
    def check_database_configuration(
        self,
        *,
        database_url: str,
        require_postgresql: bool = True,
    ) -> dict[str, Any]:
        normalized = database_url.strip().lower()
        is_postgresql = normalized.startswith(
            ("postgresql://", "postgresql+")
        )
        configured = bool(normalized)
        valid = configured and (
            is_postgresql or not require_postgresql
        )
        return {
            "valid": valid,
            "configured": configured,
            "is_postgresql": is_postgresql,
            "reason": (
                "DATABASE_CONFIGURATION_VALID"
                if valid
                else "DATABASE_CONFIGURATION_INVALID"
            ),
        }

    # RC302
    def validate_transaction_boundary(
        self,
        *,
        writes: list[dict[str, Any]],
        committed: bool,
        rollback_requested: bool,
    ) -> dict[str, Any]:
        if rollback_requested and committed:
            return {
                "valid": False,
                "reason": "COMMIT_AFTER_ROLLBACK",
            }

        applied_count = len(writes) if committed else 0
        return {
            "valid": True,
            "committed": committed,
            "applied_count": applied_count,
            "rolled_back_count": (
                len(writes)
                if rollback_requested
                else 0
            ),
        }

    # RC303
    def create_restart_marker(
        self,
        *,
        service_name: str,
        persistent_state_hash: str,
    ) -> dict[str, Any]:
        marker = {
            "marker_id": str(uuid4()),
            "service_name": service_name,
            "persistent_state_hash": persistent_state_hash,
            "created_at": now_iso(),
        }
        self._restart_markers[service_name] = marker
        return {
            "created": True,
            "marker": deepcopy(marker),
        }

    def verify_restart_marker(
        self,
        *,
        service_name: str,
        persistent_state_hash: str,
    ) -> dict[str, Any]:
        marker = self._restart_markers.get(service_name)
        if marker is None:
            return {
                "verified": False,
                "reason": "MARKER_NOT_FOUND",
            }

        verified = (
            marker["persistent_state_hash"]
            == persistent_state_hash
        )

        return {
            "verified": verified,
            "reason": (
                "PERSISTENCE_VERIFIED"
                if verified
                else "STATE_HASH_MISMATCH"
            ),
        }

    # RC304
    def evaluate_connection_pool(
        self,
        *,
        pool_size: int,
        max_overflow: int,
        active_connections: int,
    ) -> dict[str, Any]:
        capacity = max(pool_size, 0) + max(max_overflow, 0)
        utilization = (
            active_connections / capacity
            if capacity > 0
            else 1.0
        )

        if utilization >= 0.9:
            status = "CRITICAL"
        elif utilization >= 0.75:
            status = "WARNING"
        else:
            status = "HEALTHY"

        return {
            "capacity": capacity,
            "active_connections": active_connections,
            "utilization": round(utilization, 4),
            "status": status,
        }

    # RC305
    def validate_migration_state(
        self,
        *,
        expected_head: str,
        current_head: str,
        branch_count: int,
    ) -> dict[str, Any]:
        valid = (
            expected_head == current_head
            and branch_count == 1
        )
        return {
            "valid": valid,
            "expected_head": expected_head,
            "current_head": current_head,
            "branch_count": branch_count,
            "reason": (
                "MIGRATION_STATE_VALID"
                if valid
                else "MIGRATION_STATE_INVALID"
            ),
        }

    # RC306
    def validate_idempotent_write(
        self,
        *,
        idempotency_key: str,
        existing_keys: list[str],
    ) -> dict[str, Any]:
        duplicate = idempotency_key in set(existing_keys)
        return {
            "allowed": not duplicate,
            "duplicate": duplicate,
            "reason": (
                "IDEMPOTENCY_KEY_AVAILABLE"
                if not duplicate
                else "DUPLICATE_WRITE_BLOCKED"
            ),
        }

    # RC307
    def evaluate_data_retention(
        self,
        *,
        created_at: str,
        retention_days: int,
        reference_time: str,
        protected: bool = False,
    ) -> dict[str, Any]:
        created = datetime.fromisoformat(created_at)
        reference = datetime.fromisoformat(reference_time)
        expired = (
            created
            < reference
            - timedelta(days=max(retention_days, 0))
        )

        return {
            "delete": expired and not protected,
            "expired": expired,
            "protected": protected,
        }

    # RC308
    def calculate_integrity_hash(
        self,
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return {
            "hash": sha256(
                serialized.encode("utf-8")
            ).hexdigest(),
            "algorithm": "sha256",
        }

    # RC309
    def evaluate_read_replica(
        self,
        *,
        primary_lsn: int,
        replica_lsn: int,
        maximum_lag: int,
    ) -> dict[str, Any]:
        lag = max(primary_lsn - replica_lsn, 0)
        healthy = lag <= maximum_lag
        return {
            "healthy": healthy,
            "lag": lag,
            "maximum_lag": maximum_lag,
        }

    # RC310
    def build_persistence_readiness(
        self,
        *,
        database_config_valid: bool,
        migration_valid: bool,
        pool_status: str,
        restart_verified: bool,
        integrity_healthy: bool,
    ) -> dict[str, Any]:
        checks = {
            "database_config": database_config_valid,
            "migration": migration_valid,
            "pool": pool_status != "CRITICAL",
            "restart": restart_verified,
            "integrity": integrity_healthy,
        }
        failed = [
            name for name, passed in checks.items()
            if not passed
        ]
        return {
            "ready": not failed,
            "checks": checks,
            "failed_checks": failed,
        }

    # RC311
    def register_connector_check(
        self,
        *,
        connector_id: str,
        reachable: bool,
        authenticated: bool,
        schema_valid: bool,
        latency_ms: float,
    ) -> dict[str, Any]:
        healthy = (
            reachable
            and authenticated
            and schema_valid
        )
        item = {
            "connector_id": connector_id,
            "reachable": reachable,
            "authenticated": authenticated,
            "schema_valid": schema_valid,
            "latency_ms": float(latency_ms),
            "healthy": healthy,
            "checked_at": now_iso(),
        }
        self._connector_checks[connector_id] = item
        return deepcopy(item)

    # RC312
    def validate_connector_credentials(
        self,
        *,
        credential_name: str,
        value: str | None,
        minimum_length: int = 8,
    ) -> dict[str, Any]:
        present = bool(value and value.strip())
        valid = present and len(value.strip()) >= minimum_length
        return {
            "credential_name": credential_name,
            "present": present,
            "valid": valid,
        }

    # RC313
    def register_secret_reference(
        self,
        *,
        secret_name: str,
        provider: str,
        reference: str,
    ) -> dict[str, Any]:
        if not reference or reference == secret_name:
            return {
                "registered": False,
                "reason": "INVALID_SECRET_REFERENCE",
            }

        item = {
            "secret_name": secret_name,
            "provider": provider,
            "reference": reference,
            "registered_at": now_iso(),
        }
        self._secrets[secret_name] = item
        return {
            "registered": True,
            "secret": deepcopy(item),
        }

    # RC314
    def detect_secret_leak(
        self,
        *,
        text: str,
    ) -> dict[str, Any]:
        patterns = [
            r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
            r"(?i)secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
            r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        ]
        matches = []
        for pattern in patterns:
            matches.extend(
                re.findall(pattern, text)
            )
        return {
            "leak_detected": bool(matches),
            "match_count": len(matches),
        }

    # RC315
    def evaluate_connector_retry(
        self,
        *,
        attempt_number: int,
        max_attempts: int,
        base_delay_seconds: int,
    ) -> dict[str, Any]:
        retry = attempt_number < max_attempts
        delay = (
            base_delay_seconds
            * (2 ** max(attempt_number - 1, 0))
            if retry
            else 0
        )
        return {
            "retry": retry,
            "delay_seconds": delay,
        }

    # RC316
    def evaluate_connector_circuit(
        self,
        *,
        failure_count: int,
        failure_threshold: int,
    ) -> dict[str, Any]:
        open_circuit = (
            failure_count >= failure_threshold
        )
        return {
            "state": (
                "OPEN"
                if open_circuit
                else "CLOSED"
            ),
            "allow_request": not open_circuit,
        }

    # RC317
    def evaluate_connector_rate_limit(
        self,
        *,
        requests_made: int,
        request_limit: int,
    ) -> dict[str, Any]:
        allowed = requests_made < request_limit
        return {
            "allowed": allowed,
            "remaining": max(
                request_limit - requests_made,
                0,
            ),
        }

    # RC318
    def build_connector_readiness(
        self,
        *,
        required_connector_ids: list[str],
    ) -> dict[str, Any]:
        missing = [
            item
            for item in required_connector_ids
            if item not in self._connector_checks
        ]
        unhealthy = [
            item
            for item in required_connector_ids
            if item in self._connector_checks
            and not self._connector_checks[item][
                "healthy"
            ]
        ]
        return {
            "ready": not missing and not unhealthy,
            "missing": missing,
            "unhealthy": unhealthy,
        }

    # RC319
    def evaluate_rate_limit(
        self,
        *,
        request_count: int,
        limit: int,
    ) -> dict[str, Any]:
        allowed = request_count < limit
        return {
            "allowed": allowed,
            "retry_after_seconds": (
                0 if allowed else 60
            ),
        }

    # RC320
    def evaluate_authorization(
        self,
        *,
        user_roles: list[str],
        required_roles: list[str],
    ) -> dict[str, Any]:
        granted = bool(
            set(user_roles).intersection(
                required_roles
            )
        )
        return {
            "granted": granted,
            "reason": (
                "AUTHORIZED"
                if granted
                else "FORBIDDEN"
            ),
        }

    # RC321
    def validate_cors(
        self,
        *,
        allowed_origins: list[str],
        production: bool,
    ) -> dict[str, Any]:
        wildcard = "*" in allowed_origins
        valid = not (
            production and wildcard
        )
        return {
            "valid": valid,
            "wildcard_present": wildcard,
        }

    # RC322
    def build_security_headers(self) -> dict[str, Any]:
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=()"
            ),
            "Content-Security-Policy": (
                "default-src 'self'"
            ),
        }
        return {
            "headers": headers,
            "complete": len(headers) == 5,
        }

    # RC323
    def validate_password_policy(
        self,
        *,
        password: str,
        minimum_length: int = 12,
    ) -> dict[str, Any]:
        checks = {
            "length": len(password) >= minimum_length,
            "uppercase": bool(re.search(
                r"[A-Z]", password
            )),
            "lowercase": bool(re.search(
                r"[a-z]", password
            )),
            "digit": bool(re.search(
                r"\d", password
            )),
            "special": bool(re.search(
                r"[^A-Za-z0-9]", password
            )),
        }
        return {
            "valid": all(checks.values()),
            "checks": checks,
        }

    # RC324
    def build_security_readiness(
        self,
        *,
        rate_limit_enabled: bool,
        authorization_enabled: bool,
        cors_valid: bool,
        security_headers_complete: bool,
        secret_leak_detected: bool,
    ) -> dict[str, Any]:
        checks = {
            "rate_limit": rate_limit_enabled,
            "authorization": authorization_enabled,
            "cors": cors_valid,
            "headers": security_headers_complete,
            "secret_leak": (
                not secret_leak_detected
            ),
        }
        failed = [
            name for name, value in checks.items()
            if not value
        ]
        return {
            "ready": not failed,
            "failed_checks": failed,
        }

    # RC325
    def register_deployment(
        self,
        *,
        deployment_id: str,
        image_tag: str,
        environment: str,
    ) -> dict[str, Any]:
        item = {
            "deployment_id": deployment_id,
            "image_tag": image_tag,
            "environment": environment,
            "status": "CREATED",
            "created_at": now_iso(),
        }
        self._deployments[deployment_id] = item
        return {
            "registered": True,
            "deployment": deepcopy(item),
        }

    # RC326
    def evaluate_container_image(
        self,
        *,
        image_tag: str,
        digest: str,
        non_root_user: bool,
        healthcheck_present: bool,
    ) -> dict[str, Any]:
        valid = (
            bool(image_tag)
            and digest.startswith("sha256:")
            and non_root_user
            and healthcheck_present
        )
        return {
            "valid": valid,
            "image_tag": image_tag,
        }

    # RC327
    def evaluate_tls(
        self,
        *,
        enabled: bool,
        certificate_valid: bool,
        days_until_expiry: int,
    ) -> dict[str, Any]:
        valid = (
            enabled
            and certificate_valid
            and days_until_expiry > 14
        )
        return {
            "valid": valid,
            "renewal_required": (
                days_until_expiry <= 30
            ),
        }

    # RC328
    def evaluate_health_endpoints(
        self,
        *,
        health_ok: bool,
        readiness_ok: bool,
        liveness_ok: bool,
    ) -> dict[str, Any]:
        return {
            "valid": (
                health_ok
                and readiness_ok
                and liveness_ok
            ),
            "health_ok": health_ok,
            "readiness_ok": readiness_ok,
            "liveness_ok": liveness_ok,
        }

    # RC329
    def create_rollback_plan(
        self,
        *,
        deployment_id: str,
        previous_image_tag: str,
        migration_reversible: bool,
    ) -> dict[str, Any]:
        plan = {
            "rollback_plan_id": str(uuid4()),
            "deployment_id": deployment_id,
            "previous_image_tag": (
                previous_image_tag
            ),
            "migration_reversible": (
                migration_reversible
            ),
            "executable": bool(
                previous_image_tag
                and migration_reversible
            ),
        }
        return {
            "created": True,
            "plan": plan,
        }

    # RC330
    def build_deployment_readiness(
        self,
        *,
        image_valid: bool,
        tls_valid: bool,
        health_endpoints_valid: bool,
        rollback_executable: bool,
    ) -> dict[str, Any]:
        checks = {
            "image": image_valid,
            "tls": tls_valid,
            "health": health_endpoints_valid,
            "rollback": rollback_executable,
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
        }

    # RC331
    def register_backup(
        self,
        *,
        backup_id: str,
        database_name: str,
        size_bytes: int,
        checksum: str,
    ) -> dict[str, Any]:
        item = {
            "backup_id": backup_id,
            "database_name": database_name,
            "size_bytes": int(size_bytes),
            "checksum": checksum,
            "status": "AVAILABLE",
            "created_at": now_iso(),
        }
        self._backups[backup_id] = item
        return {
            "registered": True,
            "backup": deepcopy(item),
        }

    # RC332
    def verify_backup(
        self,
        *,
        backup_id: str,
        observed_checksum: str,
        minimum_size_bytes: int = 1,
    ) -> dict[str, Any]:
        backup = self._backups.get(backup_id)
        if backup is None:
            return {
                "verified": False,
                "reason": "BACKUP_NOT_FOUND",
            }

        verified = (
            backup["checksum"]
            == observed_checksum
            and backup["size_bytes"]
            >= minimum_size_bytes
        )
        return {
            "verified": verified,
            "reason": (
                "BACKUP_VALID"
                if verified
                else "BACKUP_INVALID"
            ),
        }

    # RC333
    def record_restore_drill(
        self,
        *,
        backup_id: str,
        restored: bool,
        integrity_healthy: bool,
        duration_seconds: float,
    ) -> dict[str, Any]:
        successful = (
            restored
            and integrity_healthy
        )
        item = {
            "drill_id": str(uuid4()),
            "backup_id": backup_id,
            "successful": successful,
            "integrity_healthy": (
                integrity_healthy
            ),
            "duration_seconds": float(
                duration_seconds
            ),
            "created_at": now_iso(),
        }
        self._restore_drills.append(item)
        return {
            "recorded": True,
            "drill": deepcopy(item),
        }

    # RC334
    def evaluate_disaster_recovery(
        self,
        *,
        target_rpo_minutes: int,
        actual_rpo_minutes: int,
        target_rto_minutes: int,
        actual_rto_minutes: int,
    ) -> dict[str, Any]:
        rpo_met = (
            actual_rpo_minutes
            <= target_rpo_minutes
        )
        rto_met = (
            actual_rto_minutes
            <= target_rto_minutes
        )
        return {
            "ready": rpo_met and rto_met,
            "rpo_met": rpo_met,
            "rto_met": rto_met,
        }

    # RC335
    def build_backup_readiness(
        self,
        *,
        recent_backup_verified: bool,
        restore_drill_successful: bool,
        disaster_recovery_ready: bool,
    ) -> dict[str, Any]:
        checks = {
            "backup": recent_backup_verified,
            "restore": restore_drill_successful,
            "dr": disaster_recovery_ready,
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
        }

    # RC336
    def record_smoke_test(
        self,
        *,
        test_name: str,
        passed: bool,
        details: str = "",
    ) -> dict[str, Any]:
        item = {
            "smoke_test_id": str(uuid4()),
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "created_at": now_iso(),
        }
        self._smoke_runs.append(item)
        return {
            "recorded": True,
            "test": deepcopy(item),
        }

    # RC337
    def evaluate_load_test(
        self,
        *,
        requests_per_second: float,
        error_rate: float,
        p95_latency_ms: float,
        minimum_rps: float,
        maximum_error_rate: float,
        maximum_p95_latency_ms: float,
    ) -> dict[str, Any]:
        checks = {
            "rps": (
                requests_per_second
                >= minimum_rps
            ),
            "error_rate": (
                error_rate
                <= maximum_error_rate
            ),
            "latency": (
                p95_latency_ms
                <= maximum_p95_latency_ms
            ),
        }
        item = {
            "load_run_id": str(uuid4()),
            "passed": all(checks.values()),
            "checks": checks,
            "requests_per_second": (
                requests_per_second
            ),
            "error_rate": error_rate,
            "p95_latency_ms": p95_latency_ms,
            "created_at": now_iso(),
        }
        self._load_runs.append(item)
        return deepcopy(item)

    # RC338
    def register_release_check(
        self,
        *,
        check_name: str,
        passed: bool,
        details: str = "",
    ) -> dict[str, Any]:
        item = {
            "check_name": check_name,
            "passed": passed,
            "details": details,
            "updated_at": now_iso(),
        }
        self._release_checks[
            check_name
        ] = item
        return {
            "registered": True,
            "check": deepcopy(item),
        }

    # RC339
    def evaluate_go_no_go(
        self,
        *,
        required_checks: list[str],
        minimum_smoke_pass_rate: float = 1.0,
        load_test_required: bool = True,
    ) -> dict[str, Any]:
        missing = [
            name
            for name in required_checks
            if name not in self._release_checks
        ]
        failed = [
            name
            for name in required_checks
            if name in self._release_checks
            and not self._release_checks[name][
                "passed"
            ]
        ]

        smoke_pass_rate = (
            sum(
                1
                for item in self._smoke_runs
                if item["passed"]
            )
            / len(self._smoke_runs)
            if self._smoke_runs
            else 0.0
        )

        load_passed = (
            any(
                item["passed"]
                for item in self._load_runs
            )
            if load_test_required
            else True
        )

        go = (
            not missing
            and not failed
            and smoke_pass_rate
            >= minimum_smoke_pass_rate
            and load_passed
        )

        return {
            "decision": "GO" if go else "NO_GO",
            "missing_checks": missing,
            "failed_checks": failed,
            "smoke_pass_rate": round(
                smoke_pass_rate,
                4,
            ),
            "load_test_passed": load_passed,
        }

    # RC340
    def build_release_manifest(
        self,
        *,
        version: str,
        commit_sha: str,
        image_digest: str,
        go_no_go_decision: str,
    ) -> dict[str, Any]:
        publishable = (
            go_no_go_decision == "GO"
            and bool(version)
            and bool(commit_sha)
            and image_digest.startswith(
                "sha256:"
            )
        )

        manifest = {
            "manifest_id": str(uuid4()),
            "version": version,
            "commit_sha": commit_sha,
            "image_digest": image_digest,
            "go_no_go_decision": (
                go_no_go_decision
            ),
            "publishable": publishable,
            "generated_at": now_iso(),
        }

        return {
            "generated": True,
            "manifest": manifest,
            "release_status": (
                "RELEASE_CANDIDATE_APPROVED"
                if publishable
                else "RELEASE_BLOCKED"
            ),
        }
