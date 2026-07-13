from app.domains.production_launch.service import ProductionLaunchService


def test_rc328_health_endpoints():
    s = ProductionLaunchService()
    assert s.evaluate_health_endpoints(health_ok=True,readiness_ok=True,liveness_ok=True)["valid"] is True
