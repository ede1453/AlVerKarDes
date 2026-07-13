from app.domains.production_launch.service import ProductionLaunchService


def test_rc325_deployment_register():
    s = ProductionLaunchService()
    assert s.register_deployment(deployment_id="d1",image_tag="aici:1.0",environment="production")["registered"] is True
