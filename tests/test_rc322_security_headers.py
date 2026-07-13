from app.domains.production_launch.service import ProductionLaunchService


def test_rc322_security_headers():
    s = ProductionLaunchService()
    assert s.build_security_headers()["complete"] is True
