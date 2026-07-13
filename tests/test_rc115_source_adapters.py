from app.domains.commerce_ingestion.source_adapters import (
    SourceAdapterFactory,
)


def test_rc115_fixture_adapter():
    adapter = SourceAdapterFactory.create("fixture_json")
    items = adapter.collect({
        "fixture_path": "tests/fixtures/commerce_ingestion/amazon_de_sample.json"
    })
    assert len(items) == 2
    assert items[0]["external_offer_id"] == "amazon-001"

def test_rc115_affiliate_adapter():
    content = '{"products":[{"id":"1","title":"Laptop","url":"https://x.test","price":999,"currency":"EUR"}]}'
    items = SourceAdapterFactory.create("affiliate_feed").collect({"content": content})
    assert items[0]["external_offer_id"] == "1"
