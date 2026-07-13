class ProviderRoutingPolicy:
    SUCCESS_STATUSES = {"COMPLETED"}
    RETRYABLE_STATUSES = {"PROVIDER_NOT_FOUND", "PROVIDER_NOT_CONFIGURED", "NOT_IMPLEMENTED"}

    def build_provider_order(
        self,
        *,
        preferred_provider: str,
        fallback_providers: list[str],
    ) -> list[str]:
        providers = [preferred_provider] + list(fallback_providers)
        result = []
        seen = set()

        for provider in providers:
            if provider and provider not in seen:
                seen.add(provider)
                result.append(provider)

        return result

    def is_success(self, status: str) -> bool:
        return status in self.SUCCESS_STATUSES

    def should_try_next(self, status: str) -> bool:
        return status in self.RETRYABLE_STATUSES
