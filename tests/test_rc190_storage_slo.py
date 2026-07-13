from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService


def test_rc190_healthy_slo_sample():
    service = StorageReliabilityGovernanceService()

    result = service.record_slo_sample(
        availability_pct=99.95,
        backup_success_pct=100,
        restore_success_pct=100,
        outbox_delivery_pct=99.9,
    )

    assert result["sample"]["healthy"] is True
    assert result["sample"]["breach_count"] == 0


def test_rc190_slo_breach():
    service = StorageReliabilityGovernanceService()

    result = service.record_slo_sample(
        availability_pct=99.0,
        backup_success_pct=95,
        restore_success_pct=90,
        outbox_delivery_pct=98,
    )

    assert result["sample"]["healthy"] is False
    assert result["sample"]["breach_count"] == 4
