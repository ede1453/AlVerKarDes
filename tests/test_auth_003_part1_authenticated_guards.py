"""AUTH-003 Part 1: the 29 endpoints classified AUTHENTICATED in
04-API/Endpoint-Siniflandirma-Matrisi.md now require a valid access token
(app.domains.identity.dependencies.get_current_user). Before this change none
of them checked for a token at all.

Only a representative sample is exercised here (one per guarded router file),
not all 29 — each router wires the same shared dependency, so per-router
coverage catches a regression in either the dependency itself or a specific
router's wiring without duplicating the same assertion 29 times.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import engine as db_engine
from app.main import app


@pytest.fixture(autouse=True)
def _dispose_db_engine_after_test():
    yield
    import asyncio

    asyncio.run(db_engine.dispose())


def _fresh_access_token(client: TestClient) -> str:
    email = f"auth003_p1_{uuid.uuid4().hex}@example.com"
    register = client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": "StrongPass!2345"},
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": "StrongPass!2345"},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


AUTHENTICATED_SAMPLES = [
    (
        "POST",
        "/api/v1/ai-decision-pipeline/run",
        {
            "deal_score": 80,
            "authenticity_score": 80,
            "recommendation": "BUY",
            "recommendation_confidence": 80,
        },
    ),
    ("POST", "/api/v1/ai-explanation/explain", {}),
    (
        "POST",
        "/api/v1/ai-shopping-agent/run",
        {"query": "laptop"},
    ),
    (
        "POST",
        "/api/v1/ai-shopping-assistant/advise",
        {},
    ),
    ("POST", "/api/v1/decision-context/build", {}),
    (
        "POST",
        "/api/v1/discount-intelligence/analyze",
        {"product_key": "p1"},
    ),
    ("POST", "/api/v1/explanations/generate", {"final_decision": "WATCH", "confidence": 50}),
    (
        "POST",
        "/api/v1/price-prediction/predict",
        {"product_key": "p1"},
    ),
    (
        "POST",
        "/api/v1/price-quality/anomaly",
        {"current_price": 10, "historical_prices": [10, 11, 9]},
    ),
    (
        "POST",
        "/api/v1/shopping-pipeline/run",
        {"user_id": "u1", "query": "laptop"},
    ),
    (
        "POST",
        "/api/v1/consumer-trust/feedback",
        {"payload": {"user_id": "u1", "recommendation_id": "r1", "feedback_type": "HELPFUL"}},
    ),
    ("GET", "/api/v1/commerce-pipeline/runs", None),
]


@pytest.mark.parametrize("method,path,body", AUTHENTICATED_SAMPLES)
def test_authenticated_endpoint_rejects_missing_token(method, path, body):
    with TestClient(app) as client:
        response = client.request(method, path, json=body)

    assert response.status_code == 401, (
        f"{method} {path} should require a token (401) but returned "
        f"{response.status_code}: {response.text}"
    )
    assert response.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.parametrize("method,path,body", AUTHENTICATED_SAMPLES)
def test_authenticated_endpoint_rejects_garbage_token(method, path, body):
    with TestClient(app) as client:
        response = client.request(
            method,
            path,
            json=body,
            headers={"Authorization": "Bearer not-a-real-token"},
        )

    assert response.status_code == 401, (
        f"{method} {path} should reject an invalid token (401) but returned "
        f"{response.status_code}: {response.text}"
    )


@pytest.mark.parametrize("method,path,body", AUTHENTICATED_SAMPLES)
def test_authenticated_endpoint_accepts_valid_token(method, path, body):
    with TestClient(app) as client:
        token = _fresh_access_token(client)
        response = client.request(
            method,
            path,
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code < 500, (
        f"{method} {path} with a valid token should not be rejected as "
        f"unauthenticated, got {response.status_code}: {response.text}"
    )
    assert response.status_code not in (401, 403), (
        f"{method} {path} with a genuinely valid, freshly-issued token was "
        f"still rejected as unauthenticated: {response.status_code} {response.text}"
    )
