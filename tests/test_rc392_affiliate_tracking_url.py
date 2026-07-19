from app.domains.marketplace_connectors.service import AffiliateAttributionService, AffiliateConfig


def test_rc392_affiliate_tracking_url():
    s=AffiliateAttributionService(AffiliateConfig(network="internal",publisher_id="p1",campaign_id="c1",allowed_domains=("www.ebay.de","www.idealo.de")))
    assert "publisher_id=p1" in s.build_tracking_url(destination_url="https://www.ebay.de/x")["url"]
