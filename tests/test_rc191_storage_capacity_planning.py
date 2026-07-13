from app.domains.deal_storage.production_readiness import StorageProductionReadinessService


def test_rc191_capacity_plan():
    service = StorageProductionReadinessService()
    result = service.calculate_capacity_plan(
        current_storage_gb=1000,
        used_storage_gb=500,
        daily_growth_gb=5,
        retention_days=60,
        safety_margin_pct=20,
    )
    assert result["calculated"] is True
    assert result["status"] == "HEALTHY"
    assert result["required_storage_gb"] == 960.0
    assert result["additional_storage_needed_gb"] == 0
