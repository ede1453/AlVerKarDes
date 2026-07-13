from app.domains.jobs.job_executor import JobExecutor


def test_job_executor_runs_noop():
    result = JobExecutor().execute(job_type="noop", payload={"hello": "world"})

    assert result["status"] == "COMPLETED"
    assert result["echo"] == {"hello": "world"}


def test_job_executor_runs_llm_orchestration():
    result = JobExecutor().execute(
        job_type="llm_orchestration",
        payload={
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

    assert result["status"] == "COMPLETED"
    assert result["selected_provider"] == "mock"
