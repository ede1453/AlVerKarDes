from app.domains.production_launch.service import ProductionLaunchService


def test_rc336_production_smoke():
    s = ProductionLaunchService()
    assert s.record_smoke_test(test_name="health",passed=True)["test"]["passed"] is True
