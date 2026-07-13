from app.domains.ai_explanation.explanation_prompt_builder import ExplanationPromptBuilder


def test_explanation_prompt_builder_contains_guardrails_and_version():
    prompt = ExplanationPromptBuilder().build(
        {
            "language": "en",
            "tone": "clear",
            "prompt_version": "shopping_explanation_v1",
            "agent_decision": {"decision": "BUY_NOW"},
        }
    )

    assert prompt["prompt_version"] == "shopping_explanation_v1"
    assert prompt["guardrails"]
    assert "Do not invent" in prompt["system_prompt"]
