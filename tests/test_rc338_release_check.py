from app.domains.production_launch.service import ProductionLaunchService


def test_rc338_release_check():
    s = ProductionLaunchService()
    assert s.register_release_check(check_name="security",passed=True)["registered"] is True
