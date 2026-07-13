from app.domains.production_launch.service import ProductionLaunchService


def test_rc318_connector_readiness():
    s = ProductionLaunchService()
    s.register_connector_check(connector_id="amazon",reachable=True,authenticated=True,schema_valid=True,latency_ms=100)
    assert s.build_connector_readiness(required_connector_ids=["amazon"])["ready"] is True