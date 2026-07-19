from app.domains.marketplace_connectors.service import AffiliateAttributionService, AffiliateConfig


def test_rc398_affiliate_disclosure():
    s=AffiliateAttributionService(AffiliateConfig(network="internal",publisher_id="p1",campaign_id="c1",allowed_domains=("www.ebay.de","www.idealo.de")))
    assert s.disclosure()["required"] is True
