from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_observability_vertical_slice_after_orchestration_db_audit():
    orchestration_response = client.post(
        "/api/v1/llm-orchestration/run-with-audit",
        json={
            "preferred_provider": "mock",
            "fallback_providers": [],
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain WATCH.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "WATCH",
                "assistant_context": {"product_name": "Phone"},
                "prompt_version": "shopping_v1",
            },
            "prompt_version": "shopping_v1",
        },
    )

    assert orchestration_response.status_code == 200

    snapshot_response = client.get("/api/v1/observability/snapshot")

    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()

    assert snapshot["orchestration"]["status"] == "COMPLETED"
    assert snapshot["audit"]["prompt_version"] == "shopping_v1"
