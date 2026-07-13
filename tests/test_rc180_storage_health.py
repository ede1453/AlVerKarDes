from app.domains.deal_storage.resilience import DealStorageResilienceService


def test_rc180_healthy_storage():
    service = DealStorageResilienceService()
    result = service.record_health_sample(
        database_reachable=True,
        pending_outbox_count=0,
        dead_letter_count=0,
        last_backup_age_hours=12,
        integrity_healthy=True,
    )
    assert result["sample"]["status"] == "HEALTHY"
    assert result["sample"]["score"] == 100

def test_rc180_degraded_storage():
    service = DealStorageResilienceService()
    result = service.record_health_sample(
        database_reachable=True,
        pending_outbox_count=150,
        dead_letter_count=2,
        last_backup_age_hours=60,
        integrity_healthy=True,
    )
    assert result["sample"]["status"] in {"DEGRADED", "UNHEALTHY"}
