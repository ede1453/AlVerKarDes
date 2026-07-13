from app.domains.production_launch.service import ProductionLaunchService


def test_rc314_secret_leak():
    s = ProductionLaunchService()
    assert s.detect_secret_leak(text="safe text")["leak_detected"] is False
