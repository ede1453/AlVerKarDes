from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc261_rc300_vertical_slice():
    client.post("/api/v1/growth-intelligence/clear")

    cac = client.post(
        "/api/v1/growth-intelligence/cac",
        json={"payload":{"marketing_spend":1000,"acquired_users":100}},
    ).json()
    assert cac["cac"] == 10

    dashboard = client.post(
        "/api/v1/growth-intelligence/executive-dashboard",
        json={
            "payload":{
                "mau":100,
                "dau":20,
                "activation_rate":0.5,
                "retention_rate":0.6,
                "churn_rate":0.1,
                "gmv":1000,
                "revenue":100,
                "trust_score":90,
                "growth_health_score":80
            }
        },
    ).json()
    assert dashboard["take_rate"] == 0.1
