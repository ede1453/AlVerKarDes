from app.domains.production_launch.service import ProductionLaunchService


def test_rc335_backup_readiness():
    s = ProductionLaunchService()
    assert s.build_backup_readiness(recent_backup_verified=True,restore_drill_successful=True,disaster_recovery_ready=True)["ready"] is True
