import pytest

from app.domains.watchlist.watchlist_models import WatchlistItem, create_watchlist_item_id
from app.domains.watchlist.watchlist_repository import InMemoryWatchlistRepository


@pytest.mark.asyncio
async def test_watchlist_repository_add_get_list():
    repository = InMemoryWatchlistRepository()
    item = WatchlistItem(
        id=create_watchlist_item_id(),
        user_id="user-1",
        product_key="macbook-air",
        query="MacBook Air",
    )

    await repository.add(item)

    fetched = await repository.get(item.id)
    assert fetched.product_key == "macbook-air"
    assert len(await repository.list_for_user("user-1")) == 1


@pytest.mark.asyncio
async def test_watchlist_repository_update_evaluation():
    repository = InMemoryWatchlistRepository()
    item = await repository.add(
        WatchlistItem(
            id=create_watchlist_item_id(),
            user_id="user-1",
            product_key="macbook-air",
            query="MacBook Air",
        )
    )

    updated = await repository.update_evaluation(item.id, {"target_reached": True})

    assert updated.last_evaluation["target_reached"] is True
