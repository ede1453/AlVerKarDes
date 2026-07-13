from app.domains.production_launch.service import ProductionLaunchService


def test_rc323_password_policy():
    s = ProductionLaunchService()
    assert s.validate_password_policy(password="Abcd1234!xyz")["valid"] is True
