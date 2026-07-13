from app.domains.commerce_ingestion.service import CommerceIngestionService


def test_normalize_offer():
    s = CommerceIngestionService()
    s.register_source("src","Source","api","DE","EUR")
    raw = s.collect_raw_offer("src","o1"," Apple  MacBook-Air M5 ","https://x.test",999,"EUR")["raw_offer"]
    r = s.normalize_raw_offer(raw["raw_offer_id"], "apple::macbook-air::m5")
    assert r["normalized"] is True
    assert r["offer"]["normalization_confidence"] == 100
