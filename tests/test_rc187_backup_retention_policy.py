from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService


def test_rc187_backup_retention():
    service = StorageReliabilityGovernanceService()

    service.register_backup(
        backup_id="full-old",
        backup_name="full-old",
        created_at="2026-05-01T00:00:00+00:00",
        backup_type="FULL",
    )
    service.register_backup(
        backup_id="inc-new",
        backup_name="inc-new",
        created_at="2026-07-10T00:00:00+00:00",
        backup_type="INCREMENTAL",
    )
    service.register_backup(
        backup_id="protected-old",
        backup_name="protected-old",
        created_at="2025-01-01T00:00:00+00:00",
        backup_type="FULL",
        protected=True,
    )

    result = service.evaluate_backup_retention(
        reference_time="2026-07-12T00:00:00+00:00",
        full_retention_days=30,
        incremental_retention_days=7,
    )

    assert result["delete_count"] == 1
    assert result["retain_count"] == 2
