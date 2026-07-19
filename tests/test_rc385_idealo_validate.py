from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc385_idealo_validate():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.validate_offer({"external_id":"1","title":"X","price":10,"url":"https://x"})["valid"] is True
