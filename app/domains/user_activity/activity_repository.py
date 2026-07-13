class InMemoryUserActivityRepository:
    def __init__(self):
        self._events = []

    def add(self, event):
        self._events.append(event)
        return event

    def list_for_user(self, user_id: str):
        return [event for event in self._events if event.user_id == user_id]

    def clear(self):
        self._events.clear()
