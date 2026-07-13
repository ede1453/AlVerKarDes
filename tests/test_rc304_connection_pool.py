from app.domains.production_launch.service import ProductionLaunchService


def test_rc304_connection_pool():
    s = ProductionLaunchService()
    assert s.evaluate_connection_pool(pool_size=10,max_overflow=5,active_connections=5)["status"]=="HEALTHY"
