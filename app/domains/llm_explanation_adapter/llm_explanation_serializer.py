def serialize_llm_explanation_draft(draft):
    return {
        "mode": draft.mode,
        "language": draft.language,
        "tone": draft.tone,
        "prompt_version": draft.prompt_version,
        "explanation_text": draft.explanation_text,
        "prompt": {
            "system_prompt": draft.prompt.system_prompt,
            "user_prompt": draft.prompt.user_prompt,
            "guardrails": draft.prompt.guardrails,
            "prompt_version": draft.prompt.prompt_version,
            "structured_context": draft.prompt.structured_context,
        },
    }
