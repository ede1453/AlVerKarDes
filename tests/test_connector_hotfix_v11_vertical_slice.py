from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc49_offer_is_accepted_by_aggregation():
    c = client.post("/api/v1/marketplace-connectors/search", json={
        "query":"MacBook Air","marketplace":"mock_marketplace",
        "connector":"mock_marketplace","limit":5
    })
    assert c.status_code == 200
    a = client.post("/api/v1/marketplace-aggregation/aggregate", json={
        "query":"MacBook Air","offers":c.json()["offers"]
    })
    assert a.status_code == 200
