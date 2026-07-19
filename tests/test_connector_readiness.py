from fastapi.testclient import TestClient

from app.domains.commerce_ingestion.connector_readiness import build_connector_readiness
from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_connector_readiness_reports_mock_safe_and_missing_real_credentials():
    result = build_connector_readiness({})

    assert result["status"] == "ACTION_REQUIRED"
    assert result["summary"]["connector_count"] >= 5
    mock = next(item for item in result["connectors"] if item["connector_id"] == "mock_marketplace")
    assert mock["mode"] == "mock"
    assert mock["operational_ready"] is True
    assert mock["production_ready"] is False


def test_connector_readiness_reports_missing_production_env():
    result = build_connector_readiness(
        {
            "AMAZON_CREATORS_FIXTURE_MODE": "false",
            "AMAZON_CREATORS_CLIENT_ID": "client-id",
        }
    )

    amazon = next(item for item in result["connectors"] if item["connector_id"] == "amazon_creators")
    assert amazon["mode"] == "production"
    assert amazon["operational_ready"] is False
    assert amazon["production_ready"] is False
    assert "AMAZON_CREATORS_CLIENT_SECRET" in amazon["missing_required_env"]
    assert "AMAZON_CREATORS_PARTNER_TAG" in amazon["missing_required_env"]


def test_connector_readiness_endpoint_is_registered():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        response = scoped_client.get(
            "/api/v1/connector-operations/readiness", headers=headers
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["connector_count"] >= 5
    assert any(item["connector_id"] == "mock_marketplace" for item in payload["connectors"])
