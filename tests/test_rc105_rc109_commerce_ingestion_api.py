from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)

def test_vertical_slice():
    client.post("/api/v1/commerce-ingestion/clear", headers=internal_service_headers())
    assert client.post("/api/v1/commerce-ingestion/sources", json={
        "source_id":"amazon-de","name":"Amazon Germany","source_type":"affiliate_feed",
        "country":"DE","currency":"EUR","trust_score":85}, headers=internal_service_headers()).json()["registered"]
    run = client.post("/api/v1/commerce-ingestion/runs", json={"source_id":"amazon-de"}, headers=internal_service_headers()).json()["run"]
    raw = client.post("/api/v1/commerce-ingestion/raw-offers", json={
        "source_id":"amazon-de","external_offer_id":"o1","product_title":"MacBook Air M5",
        "product_url":"https://x.test","price":999,"currency":"EUR",
        "observed_at":"2026-07-10T12:00:00+00:00"}, headers=internal_service_headers()).json()["raw_offer"]
    normalized = client.post("/api/v1/commerce-ingestion/normalize", json={
        "raw_offer_id":raw["raw_offer_id"],
        "canonical_product_key":"apple::macbook-air::m5"}, headers=internal_service_headers()).json()["offer"]
    assert client.post("/api/v1/commerce-ingestion/price-snapshots", json={"offer":normalized}, headers=internal_service_headers()).json()["ingested"]
    client.post(f"/api/v1/commerce-ingestion/runs/{run['run_id']}/complete", json={
        "collected_count":1,"ingested_count":1,"failed_count":0}, headers=internal_service_headers())
    assert client.get("/api/v1/commerce-ingestion/sources/amazon-de/health", headers=internal_service_headers()).json()["healthy"]
