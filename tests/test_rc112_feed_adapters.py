import pytest

from app.domains.commerce_ingestion.adapters import AdapterFactory


def test_rc112_csv_adapter():
    items = AdapterFactory.create("csv").parse("external_offer_id,product_title,product_url,price,currency\n1,Laptop,https://x.test,999,EUR")
    assert items[0]["external_offer_id"] == "1"

def test_rc112_json_adapter():
    items = AdapterFactory.create("json").parse('[{"external_offer_id":"1","product_title":"Laptop","product_url":"https://x.test","price":999,"currency":"EUR"}]')
    assert len(items) == 1

def test_rc112_unsupported_adapter():
    with pytest.raises(ValueError):
        AdapterFactory.create("xml")
