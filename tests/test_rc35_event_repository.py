from app.domains.events.event_models import EventCreate, create_event_record
from app.domains.events.event_repository import InMemoryEventRepository


def test_event_repository_publish_and_list():
    repository = InMemoryEventRepository()
    event = create_event_record(
        EventCreate(event_type="job.completed", source="jobs", payload={"job_id": "1"})
    )

    repository.publish(event)

    events = repository.list_recent(limit=10)

    assert len(events) == 1
    assert events[0].event_type == "job.completed"


def test_event_repository_filters_by_type_and_source():
    repository = InMemoryEventRepository()
    repository.publish(create_event_record(EventCreate(event_type="a", source="one")))
    repository.publish(create_event_record(EventCreate(event_type="b", source="two")))

    events = repository.list_recent(limit=10, event_type="b", source="two")

    assert len(events) == 1
    assert events[0].event_type == "b"
    assert events[0].source == "two"
