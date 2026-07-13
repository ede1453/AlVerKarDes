from app.domains.llm_provider_health.provider_health_service import ProviderHealthService
from app.domains.llm_provider_selection.provider_selection_models import (
    ProviderSelectionCandidate,
    ProviderSelectionRequest,
    ProviderSelectionResult,
)


class IntelligentProviderSelectionEngine:
    def __init__(self, health_service: ProviderHealthService | None = None):
        self.health_service = health_service or ProviderHealthService()

    def select(self, request: ProviderSelectionRequest) -> ProviderSelectionResult:
        health_summary = self.health_service.check(
            {
                "providers": request.candidate_providers,
                "include_external_boundaries": True,
            }
        )

        candidates = [
            self._score_provider(provider_health, request)
            for provider_health in health_summary["providers"]
        ]

        eligible = [
            candidate
            for candidate in candidates
            if self._is_eligible(candidate, request)
        ]

        sorted_candidates = sorted(
            eligible,
            key=lambda item: item.selection_score,
            reverse=True,
        )

        selected_provider = None
        fallback_providers: list[str] = []

        if sorted_candidates:
            selected_provider = sorted_candidates[0].provider
            fallback_providers = [
                candidate.provider
                for candidate in sorted_candidates[1:]
            ]

        return ProviderSelectionResult(
            selected_provider=selected_provider,
            fallback_providers=fallback_providers,
            candidates=candidates,
            strategy="health_score_latency_success_rate",
            metadata={
                "input_preferred_provider": request.preferred_provider,
                "require_available": request.require_available,
                "max_latency_ms": request.max_latency_ms,
                "health_summary_status": health_summary["status"],
            },
        )

    def _score_provider(self, provider_health: dict, request: ProviderSelectionRequest) -> ProviderSelectionCandidate:
        reasons: list[str] = []
        score = 0.0

        if provider_health["status"] == "HEALTHY":
            score += 70
            reasons.append("HEALTHY_PROVIDER")
        elif provider_health["status"] == "DEGRADED":
            score += 25
            reasons.append("DEGRADED_PROVIDER")
        else:
            reasons.append("UNAVAILABLE_PROVIDER")

        score += float(provider_health.get("success_rate", 0)) * 20

        latency_ms = int(provider_health.get("latency_ms", 0))
        if latency_ms <= 100:
            score += 10
            reasons.append("LOW_LATENCY")
        elif latency_ms <= 1000:
            score += 5
            reasons.append("ACCEPTABLE_LATENCY")
        else:
            reasons.append("HIGH_LATENCY")

        if request.preferred_provider and provider_health["provider"] == request.preferred_provider:
            score += 5
            reasons.append("PREFERRED_PROVIDER_BONUS")

        return ProviderSelectionCandidate(
            provider=provider_health["provider"],
            health_status=provider_health["status"],
            available=provider_health["available"],
            latency_ms=latency_ms,
            success_rate=float(provider_health.get("success_rate", 0)),
            selection_score=score,
            reasons=reasons,
        )

    def _is_eligible(
        self,
        candidate: ProviderSelectionCandidate,
        request: ProviderSelectionRequest,
    ) -> bool:
        if request.require_available and not candidate.available:
            return False

        if request.max_latency_ms is not None and candidate.latency_ms > request.max_latency_ms:
            return False

        return candidate.health_status != "UNAVAILABLE"
