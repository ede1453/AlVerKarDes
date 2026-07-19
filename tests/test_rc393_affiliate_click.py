from app.domains.marketplace_connectors.service import AffiliateAttributionService, AffiliateConfig


def test_rc393_affiliate_click():
    s=AffiliateAttributionService(AffiliateConfig(network="internal",publisher_id="p1",campaign_id="c1",allowed_domains=("www.ebay.de","www.idealo.de")))
    assert s.record_click(user_id="u",deal_id="d",destination_url="https://www.ebay.de/x")["recorded"] is True
