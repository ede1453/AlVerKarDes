from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_streaming_vertical_slice_from_orchestration_text():
    orchestration_response = client.post(
        "/api/v1/llm-orchestration/run",
        json={
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
    )

    assert orchestration_response.status_code == 200
    generated_text = orchestration_response.json()["generated_text"]

    preview_response = client.post(
        "/api/v1/llm-streaming/preview",
        json={
            "text": generated_text,
            "chunk_size": 12,
            "metadata": {
                "source": "orchestration",
            },
        },
    )

    assert preview_response.status_code == 200

    data = preview_response.json()

    assert data["events"][0]["event"] == "start"
    assert data["events"][-1]["event"] == "done"
    assert data["event_count"] >= 3
