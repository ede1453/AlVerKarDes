from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover - older app layouts
    get_db = None


class FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return FakeScalarResult(self._rows)


class FakeAsyncDB:
    def __init__(self):
        self.inserted_params = None
        self.rows = []
        self.committed = False

    async def execute(self, statement, params=None):
        statement_text = str(statement)

        if "INSERT INTO llm_audit_traces" in statement_text:
            self.inserted_params = dict(params or {})
            self.rows.insert(
                0,
                {
                    "id": self.inserted_params["id"],
                    "provider": self.inserted_params["provider"],
                    "model": self.inserted_params["model"],
                    "status": self.inserted_params["status"],
                    "assistant_decision": self.inserted_params["assistant_decision"],
                    "prompt_hash": self.inserted_params["prompt_hash"],
                    "prompt_version": self.inserted_params["prompt_version"],
                    "safety_warnings": [],
                    "usage": {"mock": True},
                    "metadata": {"source": "fake-db"},
                    "created_at": datetime.now(timezone.utc),
                },
            )

        return FakeResult(self.rows)

    async def commit(self):
        self.committed = True


async def override_get_db():
    yield FakeAsyncDB()


def test_llm_audit_db_endpoint_smoke_if_available_without_real_postgres():
    paths = TestClient(app).get("/openapi.json").json()["paths"]

    if "/api/v1/llm-audit-traces/db" not in paths:
        return

    if get_db is None:
        return

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/llm-audit-traces/db",
            json={
                "request_payload": {
                    "provider": "mock",
                    "model": "mock-shopping-explainer",
                    "system_prompt": "system",
                    "user_prompt": "user",
                    "structured_context": {
                        "assistant_decision": "WATCH",
                        "prompt_version": "shopping_v1",
                    },
                    "prompt_version": "shopping_v1",
                },
                "gateway_response": {
                    "provider": "mock",
                    "model": "mock-shopping-explainer",
                    "status": "COMPLETED",
                    "safety_warnings": [],
                    "usage": {"mock": True},
                    "metadata": {"prompt_version": "shopping_v1"},
                },
            },
        )

        assert response.status_code == 200
        assert response.json()["provider"] == "mock"
        assert response.json()["prompt_version"] == "shopping_v1"
    finally:
        app.dependency_overrides.clear()
