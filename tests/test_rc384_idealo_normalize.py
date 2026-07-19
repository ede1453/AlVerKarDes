from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc384_idealo_normalize():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.normalize_offer({"id":"1","title":"X","price":"10","url":"https://x"})["price"]==10
