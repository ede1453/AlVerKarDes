class LLMOrchestrationAuditAdapter:
    def build_audit_payload(
        self,
        *,
        orchestration_request: dict,
        orchestration_result: dict,
    ) -> dict:
        selected_attempt = self._select_completed_attempt(orchestration_result)

        gateway_response = {
            "provider": orchestration_result.get("selected_provider") or selected_attempt.get("provider"),
            "model": orchestration_request.get("model", "unknown"),
            "status": orchestration_result.get("status", "UNKNOWN"),
            "generated_text": orchestration_result.get("generated_text", ""),
            "safety_warnings": selected_attempt.get("safety_warnings", []),
            "usage": {
                "orchestration_attempt_count": len(orchestration_result.get("attempts", [])),
                "fallback_used": orchestration_result.get("fallback_used", False),
            },
            "metadata": {
                "orchestration_metadata": orchestration_result.get("metadata", {}),
                "selected_attempt_metadata": selected_attempt.get("metadata", {}),
                "prompt_version": orchestration_result.get("prompt_version", "shopping_v1"),
            },
        }

        request_payload = {
            "provider": orchestration_result.get("selected_provider") or orchestration_request.get("preferred_provider"),
            "model": orchestration_request.get("model", "unknown"),
            "system_prompt": orchestration_request.get("system_prompt", ""),
            "user_prompt": orchestration_request.get("user_prompt", ""),
            "guardrails": orchestration_request.get("guardrails", []),
            "structured_context": orchestration_request.get("structured_context", {}),
            "prompt_version": orchestration_result.get(
                "prompt_version",
                orchestration_request.get("prompt_version", "shopping_v1"),
            ),
        }

        return {
            "request_payload": request_payload,
            "gateway_response": gateway_response,
        }

    def _select_completed_attempt(self, orchestration_result: dict) -> dict:
        for attempt in orchestration_result.get("attempts", []):
            if attempt.get("status") == "COMPLETED":
                return attempt

        attempts = orchestration_result.get("attempts", [])
        if attempts:
            return attempts[-1]

        return {}
