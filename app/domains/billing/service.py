from typing import Any

from app.domains.billing.db_models import SubscriptionTier
from app.domains.billing.provider import PaymentProvider
from app.domains.billing.repository import SubscriptionDBRepository


class SubscriptionService:
    def __init__(
        self,
        repository: SubscriptionDBRepository,
        payment_provider: PaymentProvider | None = None,
    ):
        self.repository = repository
        self.payment_provider = payment_provider

    async def get_current(self, user_id: str) -> dict[str, Any]:
        existing = await self.repository.get(user_id)
        if existing:
            return existing

        # BILL-001 migration (0020_subscriptions) backfills every EXISTING
        # user to an explicit FREE row -- this branch is a defensive
        # default for users that somehow still have no row (e.g. a fresh
        # registration between migration and their first billing read),
        # same "synthesize a default when no row exists" pattern as
        # NotificationPreferenceService.get_preferences() (CLIENT-002g).
        return {
            "user_id": user_id,
            "tier": SubscriptionTier.FREE.value,
            "provider_reference": None,
            "updated_at": None,
        }

    async def checkout(self, *, user_id: str, plan: str) -> dict[str, Any]:
        if plan not in (SubscriptionTier.FREE.value, SubscriptionTier.PREMIUM.value):
            raise ValueError(f"invalid plan {plan!r}")

        result = await self.payment_provider.start_checkout(user_id=user_id, plan=plan)
        if not result.success:
            raise RuntimeError("payment_provider.start_checkout reported failure")

        return await self.repository.upsert(
            user_id=user_id,
            tier=plan,
            provider_reference=result.external_reference,
        )

    async def cancel(self, *, user_id: str) -> dict[str, Any]:
        await self.payment_provider.cancel_subscription(user_id=user_id)
        return await self.repository.upsert(
            user_id=user_id,
            tier=SubscriptionTier.FREE.value,
            provider_reference=None,
        )
