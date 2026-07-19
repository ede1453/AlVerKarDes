from fastapi.testclient import TestClient

from app.main import app

client=TestClient(app)
def test_rc361_rc400_openapi_paths():
    paths=client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/marketplace-connectors/ebay/health",
        "/api/v1/marketplace-connectors/ebay/search",
        "/api/v1/marketplace-connectors/idealo/health",
        "/api/v1/marketplace-connectors/idealo/feed",
        "/api/v1/marketplace-connectors/affiliate/click",
        "/api/v1/marketplace-connectors/affiliate/readiness",
    ]:
        assert path in paths
