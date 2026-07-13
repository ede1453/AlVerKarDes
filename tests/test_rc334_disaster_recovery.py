from app.domains.production_launch.service import ProductionLaunchService


def test_rc334_disaster_recovery():
    s = ProductionLaunchService()
    assert s.evaluate_disaster_recovery(target_rpo_minutes=15,actual_rpo_minutes=10,target_rto_minutes=60,actual_rto_minutes=45)["ready"] is True
