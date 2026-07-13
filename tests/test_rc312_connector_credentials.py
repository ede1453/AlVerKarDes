from app.domains.production_launch.service import ProductionLaunchService


def test_rc312_connector_credentials():
    s = ProductionLaunchService()
    assert s.validate_connector_credentials(credential_name="API_KEY",value="abcdefghijk")["valid"] is True
