from app.domains.production_launch.service import ProductionLaunchService


def test_rc307_data_retention():
    s = ProductionLaunchService()
    r=s.evaluate_data_retention(created_at="2025-01-01T00:00:00+00:00",retention_days=30,reference_time="2026-07-12T00:00:00+00:00")
    assert r["delete"] is True