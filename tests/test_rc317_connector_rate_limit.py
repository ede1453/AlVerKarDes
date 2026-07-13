from app.domains.production_launch.service import ProductionLaunchService


def test_rc317_connector_rate_limit():
    s = ProductionLaunchService()
    assert s.evaluate_connector_rate_limit(requests_made=5,request_limit=10)["allowed"] is True
