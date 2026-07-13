from app.domains.production_launch.service import ProductionLaunchService


def test_rc315_connector_retry():
    s = ProductionLaunchService()
    r=s.evaluate_connector_retry(attempt_number=2,max_attempts=5,base_delay_seconds=10)
    assert r["delay_seconds"]==20