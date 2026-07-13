from app.domains.production_launch.service import ProductionLaunchService


def test_rc321_cors():
    s = ProductionLaunchService()
    assert s.validate_cors(allowed_origins=["https://app.example.com"],production=True)["valid"] is True
