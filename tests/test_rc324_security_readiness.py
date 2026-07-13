from app.domains.production_launch.service import ProductionLaunchService


def test_rc324_security_readiness():
    s = ProductionLaunchService()
    r=s.build_security_readiness(rate_limit_enabled=True,authorization_enabled=True,cors_valid=True,security_headers_complete=True,secret_leak_detected=False)
    assert r["ready"] is True