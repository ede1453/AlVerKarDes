from app.domains.commerce_ingestion.service import CommerceIngestionService


def offer(s):
    s.register_source("src","Source","api","DE","EUR")
    raw = s.collect_raw_offer("src","o1","Laptop","https://x.test",899,"EUR",observed_at="2026-07-10T12:00:00+00:00")["raw_offer"]
    return s.normalize_raw_offer(raw["raw_offer_id"], "brand::laptop::model")["offer"]

def test_ingest_and_deduplicate_snapshot():
    s = CommerceIngestionService()
    item = offer(s)
    assert s.ingest_price_snapshot(item)["ingested"] is True
    dup = s.ingest_price_snapshot(item)
    assert dup["ingested"] is False
    assert dup["reason"] == "DUPLICATE_PRICE_SNAPSHOT"
