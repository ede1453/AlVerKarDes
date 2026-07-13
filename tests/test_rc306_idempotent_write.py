from app.domains.production_launch.service import ProductionLaunchService


def test_rc306_idempotent_write():
    s = ProductionLaunchService()
    assert s.validate_idempotent_write(idempotency_key="k1",existing_keys=["k2"])["allowed"] is True
