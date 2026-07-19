from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_mock_connector_preserves_exact_rc49_contract():
    r = client.post("/api/v1/marketplace-connectors/search", json={
        "query":"MacBook Air","marketplace":"mock_marketplace",
        "connector":"mock_marketplace","limit":5
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "COMPLETED"
    assert data["offer_count"] == 5
    assert len(data["offers"]) == 5
    assert data["offers"][0]["product_name"] == "MacBook Air"
    assert data["offers"][0]["price"] == 999.0

def test_external_connector_preserves_rc49_status():
    r = client.post("/api/v1/marketplace-connectors/search", json={
        "query":"MacBook Air","marketplace":"amazon","connector":"amazon"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "CONNECTOR_NOT_CONFIGURED"
