from app.domains.llm_audit_trace.prompt_hashing import PromptHasher


def test_prompt_hasher_is_stable_for_same_payload():
    hasher = PromptHasher()

    first = hasher.hash_prompt(
        system_prompt="system",
        user_prompt="user",
        structured_context={"b": 2, "a": 1},
    )

    second = hasher.hash_prompt(
        system_prompt="system",
        user_prompt="user",
        structured_context={"a": 1, "b": 2},
    )

    assert first == second
    assert len(first) == 64
