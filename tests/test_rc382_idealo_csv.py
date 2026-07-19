from app.domains.marketplace_connectors.service import IdealoPartnerConfig, IdealoPartnerConnectorService


def test_rc382_idealo_csv():
    s=IdealoPartnerConnectorService(IdealoPartnerConfig(partner_id="p",api_key="k",fixture_mode=True))
    assert s.parse_csv_feed("id,title\n1,X")["row_count"]==1
