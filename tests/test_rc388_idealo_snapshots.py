from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc388_idealo_snapshots():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.build_price_snapshots([{"external_id":"1","price":10,"currency":"EUR"}])["snapshot_count"]==1
