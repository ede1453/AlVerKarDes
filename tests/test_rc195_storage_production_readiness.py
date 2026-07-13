from app.domains.deal_storage.production_readiness import StorageProductionReadinessService


def test_rc195_storage_ready():
    service = StorageProductionReadinessService()
    result = service.evaluate_production_readiness(
        capacity_status="HEALTHY",
        encryption_compliant=True,
        integrity_healthy=True,
        backup_recent=True,
        restore_drill_successful=True,
        slo_healthy=True,
        pending_critical_access_issues=0,
    )
    assert result["report"]["ready"] is True
    assert result["report"]["status"] == "READY"

def test_rc195_storage_not_ready():
    service = StorageProductionReadinessService()
    result = service.evaluate_production_readiness(
        capacity_status="CRITICAL",
        encryption_compliant=False,
        integrity_healthy=False,
        backup_recent=False,
        restore_drill_successful=False,
        slo_healthy=False,
        pending_critical_access_issues=2,
    )
    assert result["report"]["ready"] is False
    assert len(result["report"]["blockers"]) >= 3
