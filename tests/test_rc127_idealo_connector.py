from app.domains.commerce_ingestion.marketplace_connectors import IdealoConnector


def test_rc127_idealo_connector():
    result = IdealoConnector().normalize({
        "offerId": "idealo-1",
        "productName": "Laptop",
        "offerUrl": "https://idealo.test/item",
        "totalPrice": 879,
        "shopName": "Shop One",
        "deliveryStatus": "ships_immediately",
    })
    assert result["marketplace"] == "idealo"
    assert result["seller_name"] == "Shop One"
