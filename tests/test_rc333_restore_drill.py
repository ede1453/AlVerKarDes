from app.domains.production_launch.service import ProductionLaunchService


def test_rc333_restore_drill():
    s = ProductionLaunchService()
    r=s.record_restore_drill(backup_id="b1",restored=True,integrity_healthy=True,duration_seconds=10)
    assert r["drill"]["successful"] is True