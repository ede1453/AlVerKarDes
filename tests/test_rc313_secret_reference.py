from app.domains.production_launch.service import ProductionLaunchService


def test_rc313_secret_reference():
    s = ProductionLaunchService()
    assert s.register_secret_reference(secret_name="API_KEY",provider="vault",reference="secret/data/api")["registered"] is True
