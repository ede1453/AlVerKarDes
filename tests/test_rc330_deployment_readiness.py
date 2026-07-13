from app.domains.production_launch.service import ProductionLaunchService


def test_rc330_deployment_readiness():
    s = ProductionLaunchService()
    r=s.build_deployment_readiness(image_valid=True,tls_valid=True,health_endpoints_valid=True,rollback_executable=True)
    assert r["ready"] is True