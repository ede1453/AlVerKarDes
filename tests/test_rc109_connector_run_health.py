from app.domains.commerce_ingestion.service import CommerceIngestionService


def test_connector_health_after_success():
    s = CommerceIngestionService()
    s.register_source("src","Source","api","DE","EUR")
    run = s.start_connector_run("src")["run"]
    s.complete_connector_run(run["run_id"], 10, 8, 2)
    health = s.get_connector_health("src")
    assert health["healthy"] is True
    assert health["status"] == "HEALTHY"

def test_failed_run_unhealthy():
    s = CommerceIngestionService()
    s.register_source("src","Source","api","DE","EUR")
    run = s.start_connector_run("src")["run"]
    s.complete_connector_run(run["run_id"], 0, 0, 1, "TIMEOUT")
    assert s.get_connector_health("src")["status"] == "UNHEALTHY"
