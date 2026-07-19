from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc386_idealo_feed_normalize():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.normalize_feed([{"id":"1","title":"X","price":"10","url":"https://x"}])["accepted_count"]==1
