from app.domains.commerce_ingestion.service import CommerceIngestionService


def test_register_and_filter_source():
    s = CommerceIngestionService()
    assert s.register_source("amazon-de","Amazon Germany","affiliate_feed","DE","EUR",trust_score=85)["registered"]
    assert s.list_sources(country="DE")["source_count"] == 1

def test_reject_unsupported_source_type():
    s = CommerceIngestionService()
    r = s.register_source("bad","Bad","scraper","DE","EUR")
    assert r["registered"] is False
    assert r["reason"] == "UNSUPPORTED_SOURCE_TYPE"
