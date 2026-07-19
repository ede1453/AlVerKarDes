from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc135_rc139_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post(
            "/api/v1/production-http/clear",
            headers=headers,
        )

        client.post(
            "/api/v1/production-http/fixture-pages",
            headers=headers,
            json={
                "url":"https://example.test/page/1",
                "body":"{\"items\":[{\"id\":\"1\"}],\"next\":\"https://example.test/page/2\"}",
            },
        )

        client.post(
            "/api/v1/production-http/fixture-pages",
            headers=headers,
            json={
                "url":"https://example.test/page/2",
                "body":"{\"items\":[{\"id\":\"2\"}]}",
            },
        )

        response = client.post(
            "/api/v1/production-http/execute",
            headers=headers,
            json={
                "start_url":"https://example.test/page/1",
                "max_pages":5,
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["executed"] is True
    assert data["page_count"] == 2
    assert data["item_count"] == 2
