from app.domains.deal_storage.production_readiness import StorageProductionReadinessService


def test_rc192_encryption_compliant():
    service = StorageProductionReadinessService()
    service.register_encryption_policy(
        policy_id="prod",
        encryption_at_rest=True,
        encryption_in_transit=True,
        key_provider="vault",
        key_reference="secret/data/storage-key",
        rotation_days=90,
    )
    result = service.evaluate_encryption_compliance(
        policy_id="prod",
        key_age_days=30,
        tls_enabled=True,
        volume_encrypted=True,
    )
    assert result["compliant"] is True

def test_rc192_rotation_overdue():
    service = StorageProductionReadinessService()
    service.register_encryption_policy(
        policy_id="prod",
        encryption_at_rest=True,
        encryption_in_transit=True,
        key_provider="vault",
        key_reference="secret/data/storage-key",
        rotation_days=90,
    )
    result = service.evaluate_encryption_compliance(
        policy_id="prod",
        key_age_days=120,
        tls_enabled=True,
        volume_encrypted=True,
    )
    assert result["compliant"] is False
    assert "KEY_ROTATION_OVERDUE" in result["issues"]
