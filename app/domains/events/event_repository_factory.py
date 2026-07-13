from app.domains.events.event_repository import InMemoryEventRepository

_EVENT_REPOSITORY = InMemoryEventRepository()


def get_event_repository() -> InMemoryEventRepository:
    return _EVENT_REPOSITORY


def reset_event_repository():
    _EVENT_REPOSITORY.clear()
    return _EVENT_REPOSITORY
