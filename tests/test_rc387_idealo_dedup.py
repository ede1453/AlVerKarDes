from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc387_idealo_dedup():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.deduplicate_offers([{"external_id":"1","effective_price":10,"currency":"EUR"},{"external_id":"1","effective_price":10,"currency":"EUR"}])["output_count"]==1
