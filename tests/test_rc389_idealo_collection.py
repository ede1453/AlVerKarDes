from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc389_idealo_collection():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.run_feed_collection(content="id,title,price,url\n1,X,10,https://x")["executed"] is True
