from app.domains.watchlist.watchlist_models import WatchlistItem, create_watchlist_item_id
from app.domains.watchlist.watchlist_repository import InMemoryWatchlistRepository


def test_watchlist_repository_add_get_list():
    repository = InMemoryWatchlistRepository()
    item = WatchlistItem(
        id=create_watchlist_item_id(),
        user_id="user-1",
        product_key="macbook-air",
        query="MacBook Air",
    )

    repository.add(item)

    assert repository.get(item.id).product_key == "macbook-air"
    assert len(repository.list_for_user("user-1")) == 1


def test_watchlist_repository_update_evaluation():
    repository = InMemoryWatchlistRepository()
    item = repository.add(
        WatchlistItem(
            id=create_watchlist_item_id(),
            user_id="user-1",
            product_key="macbook-air",
            query="MacBook Air",
        )
    )

    updated = repository.update_evaluation(item.id, {"target_reached": True})

    assert updated.last_evaluation["target_reached"] is True
