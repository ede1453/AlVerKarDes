from app.domains.commerce_ingestion.marketplace_connectors import AffiliateNetworkConnector


def test_rc128_affiliate_connector():
    result = AffiliateNetworkConnector().normalize({
        "network": "awin",
        "offer_id": "aff-1",
        "product_name": "Laptop",
        "tracking_url": "https://affiliate.test/item",
        "sale_price": 850,
        "advertiser_name": "Retailer",
    })
    assert result["marketplace"] == "awin"
    assert result["price"] == 850
