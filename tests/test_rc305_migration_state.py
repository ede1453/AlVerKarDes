from app.domains.production_launch.service import ProductionLaunchService


def test_rc305_migration_state():
    s = ProductionLaunchService()
    assert s.validate_migration_state(expected_head="0014",current_head="0014",branch_count=1)["valid"] is True
