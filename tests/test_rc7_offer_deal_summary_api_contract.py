from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_offer_deal_summary_endpoint_exists_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/deals/offers/{offer_id}/summary" in paths
    assert "get" in paths["/api/v1/deals/offers/{offer_id}/summary"]
