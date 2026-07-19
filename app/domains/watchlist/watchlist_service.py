from decimal import Decimal

from app.domains.events.event_bus_service import EventBusService
from app.domains.smart_alerts.smart_alert_service import SmartAlertService
from app.domains.watchlist.watchlist_models import WatchlistItem, create_watchlist_item_id
from app.domains.watchlist.watchlist_repository import InMemoryWatchlistRepository, WatchlistItemDBRepository
from app.domains.watchlist.watchlist_serializer import serialize_watchlist_item


class WatchlistService:
    def __init__(
        self,
        repository: InMemoryWatchlistRepository | WatchlistItemDBRepository | None = None,
        smart_alert_service: SmartAlertService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.repository = repository or InMemoryWatchlistRepository()
        self.smart_alert_service = smart_alert_service or SmartAlertService()
        self.event_bus_service = event_bus_service or EventBusService()

    async def add_item(self, payload: dict):
        item = WatchlistItem(
            id=create_watchlist_item_id(),
            user_id=payload["user_id"],
            product_key=payload["product_key"],
            query=payload["query"],
            target_price=payload.get("target_price"),
            marketplaces=payload.get("marketplaces", []),
            channels=payload.get("channels", ["in_app"]),
            metadata=payload.get("metadata", {}),
        )
        saved = await self.repository.add(item)

        self.event_bus_service.publish(
            {
                "event_type": "watchlist.item_added",
                "source": "watchlist",
                "payload": {
                    "watchlist_item_id": saved.id,
                    "user_id": saved.user_id,
                    "product_key": saved.product_key,
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialize_watchlist_item(saved)

    async def get_item(self, item_id: str):
        item = await self.repository.get(item_id)
        if item is None:
            return None
        return serialize_watchlist_item(item)

    async def list_for_user(self, user_id: str):
        return [serialize_watchlist_item(item) for item in await self.repository.list_for_user(user_id)]

    async def evaluate_item(self, item_id: str, payload: dict):
        item = await self.repository.get(item_id)
        if item is None:
            return None

        deal_detection = payload.get("deal_detection")
        price_prediction = payload.get("price_prediction")
        personalization = payload.get("personalization")

        alert = self.smart_alert_service.evaluate(
            {
                "user_id": item.user_id,
                "product_key": item.product_key,
                "deal_detection": deal_detection,
                "price_prediction": price_prediction,
                "personalization": personalization,
                "channels": item.channels,
            }
        )

        target_reached = False
        latest_price = None
        if payload.get("price_history"):
            latest_price = payload["price_history"].get("latest_price")

        if item.target_price is not None and latest_price is not None:
            target_reached = Decimal(str(latest_price)) <= Decimal(str(item.target_price))

        evaluation = {
            "smart_alert": alert,
            "target_reached": target_reached,
            "latest_price": latest_price,
            "evaluation_version": "watchlist_eval_v1",
        }

        updated = await self.repository.update_evaluation(item_id, evaluation)

        self.event_bus_service.publish(
            {
                "event_type": "watchlist.item_evaluated",
                "source": "watchlist",
                "payload": {
                    "watchlist_item_id": item.id,
                    "user_id": item.user_id,
                    "product_key": item.product_key,
                    "should_alert": alert["should_alert"],
                    "target_reached": target_reached,
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialize_watchlist_item(updated)

    async def deactivate_item(self, item_id: str):
        item = await self.repository.get(item_id)
        if item is None:
            return None
        return serialize_watchlist_item(await self.repository.deactivate(item_id))

    async def clear(self):
        await self.repository.clear()
        return {"cleared": True}
