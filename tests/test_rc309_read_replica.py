from app.domains.production_launch.service import ProductionLaunchService


def test_rc309_read_replica():
    s = ProductionLaunchService()
    assert s.evaluate_read_replica(primary_lsn=100,replica_lsn=95,maximum_lag=10)["healthy"] is True
