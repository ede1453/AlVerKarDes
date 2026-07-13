from app.domains.commerce_ingestion.service import CommerceIngestionService


def test_collect_raw_offer():
    s = CommerceIngestionService()
    s.register_source("src","Source","api","DE","EUR")
    r = s.collect_raw_offer("src","o1","Laptop","https://x.test",999,"EUR","in_stock")
    assert r["collected"] is True
    assert r["raw_offer"]["price"] == 999.0

def test_unknown_source_rejected():
    s = CommerceIngestionService()
    r = s.collect_raw_offer("missing","o1","Laptop","https://x.test",999,"EUR")
    assert r["reason"] == "SOURCE_NOT_FOUND"
