from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc383_idealo_json():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.parse_json_feed('[{"id":"1"}]')["row_count"]==1
