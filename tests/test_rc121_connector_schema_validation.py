from app.domains.commerce_ingestion.operations import ConnectorOperationsService


def test_rc121_validate_valid_and_invalid_items():
    service = ConnectorOperationsService()
    result = service.validate_source_items([
        {
            "external_offer_id":"1",
            "product_title":"Laptop",
            "product_url":"https://x.test",
            "price":999,
            "currency":"eur",
        },
        {
            "external_offer_id":"2",
            "product_title":"",
            "product_url":"https://x.test",
            "price":0,
            "currency":"EUR",
        },
    ])
    assert result["valid"] is False
    assert result["valid_count"] == 1
    assert result["invalid_count"] == 1
    assert result["valid_items"][0]["currency"] == "EUR"
