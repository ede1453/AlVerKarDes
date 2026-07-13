from app.domains.production_launch.service import ProductionLaunchService


def test_rc310_persistence_readiness():
    s = ProductionLaunchService()
    r=s.build_persistence_readiness(database_config_valid=True,migration_valid=True,pool_status="HEALTHY",restart_verified=True,integrity_healthy=True)
    assert r["ready"] is True