from app.domains.production_launch.service import ProductionLaunchService


def test_rc301_database_configuration():
    s = ProductionLaunchService()
    r=s.check_database_configuration(database_url="postgresql://user:pass@db/app")
    assert r["valid"] is True