from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_job_queue_vertical_slice_runs_orchestration_job():
    response = client.post(
        "/api/v1/jobs/run-now",
        json={
            "job_type": "llm_orchestration",
            "payload": {
                "preferred_provider": "mock",
                "fallback_providers": [],
                "system_prompt": "Explain safely.",
                "user_prompt": "Explain BUY_NOW.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "BUY_NOW",
                    "assistant_context": {"product_name": "MacBook Air"},
                    "prompt_version": "shopping_v1",
                },
                "prompt_version": "shopping_v1",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["result"]["status"] == "COMPLETED"
    assert data["result"]["selected_provider"] == "mock"
