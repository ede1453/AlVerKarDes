from app.domains.production_launch.service import ProductionLaunchService


def test_rc327_tls():
    s = ProductionLaunchService()
    assert s.evaluate_tls(enabled=True,certificate_valid=True,days_until_expiry=90)["valid"] is True
