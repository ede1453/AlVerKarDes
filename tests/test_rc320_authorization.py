from app.domains.production_launch.service import ProductionLaunchService


def test_rc320_authorization():
    s = ProductionLaunchService()
    assert s.evaluate_authorization(user_roles=["admin"],required_roles=["admin"])["granted"] is True
