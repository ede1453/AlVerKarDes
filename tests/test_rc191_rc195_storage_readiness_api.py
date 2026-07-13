from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc191_rc195_vertical_slice():
    client.post(
        "/api/v1/storage-production-readiness/clear"
    )

    capacity = client.post(
        "/api/v1/storage-production-readiness/capacity",
        json={
            "current_storage_gb":1000,
            "used_storage_gb":500,
            "daily_growth_gb":5,
            "retention_days":60,
            "safety_margin_pct":20
        },
    ).json()
    assert capacity["status"] == "HEALTHY"

    client.post(
        "/api/v1/storage-production-readiness/encryption-policies",
        json={
            "policy_id":"prod",
            "encryption_at_rest":True,
            "encryption_in_transit":True,
            "key_provider":"vault",
            "key_reference":"secret/data/storage-key",
            "rotation_days":90
        },
    )

    encryption = client.post(
        "/api/v1/storage-production-readiness/encryption-compliance",
        json={
            "policy_id":"prod",
            "key_age_days":30,
            "tls_enabled":True,
            "volume_encrypted":True
        },
    ).json()
    assert encryption["compliant"] is True

    readiness = client.post(
        "/api/v1/storage-production-readiness/readiness",
        json={
            "capacity_status":capacity["status"],
            "encryption_compliant":encryption["compliant"],
            "integrity_healthy":True,
            "backup_recent":True,
            "restore_drill_successful":True,
            "slo_healthy":True,
            "pending_critical_access_issues":0
        },
    ).json()
    assert readiness["report"]["ready"] is True
