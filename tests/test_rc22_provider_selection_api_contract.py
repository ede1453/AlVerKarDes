from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_selection_api_selects_provider():
    response = client.post(
        "/api/v1/llm-provider-selection/select",
        json={
            "candidate_providers": ["mock", "openai"],
            "require_available": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["selected_provider"] == "mock"
    assert data["candidates"]


def test_provider_selection_api_handles_no_eligible_provider():
    response = client.post(
        "/api/v1/llm-provider-selection/select",
        json={
            "candidate_providers": ["openai", "local"],
            "require_available": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["selected_provider"] is None
