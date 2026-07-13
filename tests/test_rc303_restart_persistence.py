from app.domains.production_launch.service import ProductionLaunchService


def test_rc303_restart_persistence():
    s = ProductionLaunchService()
    s.create_restart_marker(service_name="api",persistent_state_hash="abc")
    assert s.verify_restart_marker(service_name="api",persistent_state_hash="abc")["verified"] is True