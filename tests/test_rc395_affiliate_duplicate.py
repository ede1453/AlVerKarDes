from app.domains.marketplace_connectors.service import AffiliateAttributionService, AffiliateConfig


def test_rc395_affiliate_duplicate():
    s=AffiliateAttributionService(AffiliateConfig(network="internal",publisher_id="p1",campaign_id="c1",allowed_domains=("www.ebay.de","www.idealo.de")))
    c=s.record_click(user_id="u",deal_id="d",destination_url="https://www.ebay.de/x")["click"]
    s.record_conversion(click_id=c["click_id"],order_value=100,commission_value=5,external_order_id="o1")
    assert s.prevent_duplicate_conversion("o1")["allowed"] is False
