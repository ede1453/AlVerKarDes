from app.domains.production_launch.service import ProductionLaunchService


def test_rc319_api_rate_limit():
    s = ProductionLaunchService()
    assert s.evaluate_rate_limit(request_count=10,limit=10)["allowed"] is False
