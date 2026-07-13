from app.domains.production_launch.service import ProductionLaunchService


def test_rc311_connector_smoke():
    s = ProductionLaunchService()
    r=s.register_connector_check(connector_id="amazon",reachable=True,authenticated=True,schema_valid=True,latency_ms=100)
    assert r["healthy"] is True