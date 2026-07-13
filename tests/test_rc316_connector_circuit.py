from app.domains.production_launch.service import ProductionLaunchService


def test_rc316_connector_circuit():
    s = ProductionLaunchService()
    assert s.evaluate_connector_circuit(failure_count=5,failure_threshold=5)["state"]=="OPEN"
