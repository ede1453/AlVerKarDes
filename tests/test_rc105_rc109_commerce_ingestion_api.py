from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_vertical_slice():
    client.post("/api/v1/commerce-ingestion/clear")
    assert client.post("/api/v1/commerce-ingestion/sources", json={
        "source_id":"amazon-de","name":"Amazon Germany","source_type":"affiliate_feed",
        "country":"DE","currency":"EUR","trust_score":85}).json()["registered"]
    run = client.post("/api/v1/commerce-ingestion/runs", json={"source_id":"amazon-de"}).json()["run"]
    raw = client.post("/api/v1/commerce-ingestion/raw-offers", json={
        "source_id":"amazon-de","external_offer_id":"o1","product_title":"MacBook Air M5",
        "product_url":"https://x.test","price":999,"currency":"EUR",
        "observed_at":"2026-07-10T12:00:00+00:00"}).json()["raw_offer"]
    normalized = client.post("/api/v1/commerce-ingestion/normalize", json={
        "raw_offer_id":raw["raw_offer_id"],
        "canonical_product_key":"apple::macbook-air::m5"}).json()["offer"]
    assert client.post("/api/v1/commerce-ingestion/price-snapshots", json={"offer":normalized}).json()["ingested"]
    client.post(f"/api/v1/commerce-ingestion/runs/{run['run_id']}/complete", json={
        "collected_count":1,"ingested_count":1,"failed_count":0})
    assert client.get("/api/v1/commerce-ingestion/sources/amazon-de/health").json()["healthy"]
