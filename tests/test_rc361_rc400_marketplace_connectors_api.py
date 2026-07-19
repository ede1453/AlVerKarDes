from fastapi.testclient import TestClient

from app.main import app

client=TestClient(app)
def test_rc361_rc400_routes_work():
    assert client.get("/api/v1/marketplace-connectors/ebay/health").status_code==200
    r=client.post("/api/v1/marketplace-connectors/idealo/feed",json={"content":"id,title,price,url\n1,X,10,https://x","format":"csv","delimiter":","})
    assert r.status_code==200
    assert r.json()["offer_count"]==1
