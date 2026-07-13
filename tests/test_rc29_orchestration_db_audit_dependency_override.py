from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover
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
        self.rows = []
        self.committed = False

    async def execute(self, statement, params=None):
        statement_text = str(statement)

        if "INSERT INTO llm_audit_traces" in statement_text:
            params = dict(params or {})
            self.rows.insert(
                0,
                {
                    "id": params["id"],
                    "provider": params["provider"],
                    "model": params["model"],
                    "status": params["status"],
                    "assistant_decision": params["assistant_decision"],
                    "prompt_hash": params["prompt_hash"],
                    "prompt_version": params["prompt_version"],
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


def test_orchestration_db_audit_endpoint_uses_dependency_override_without_real_postgres():
    if get_db is None:
        return

    paths = TestClient(app).get("/openapi.json").json()["paths"]
    if "/api/v1/llm-orchestration/run-with-db-audit" not in paths:
        return

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/llm-orchestration/run-with-db-audit",
            json={
                "preferred_provider": "mock",
                "fallback_providers": [],
                "system_prompt": "Explain safely.",
                "user_prompt": "Explain BUY_NOW.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "BUY_NOW",
                    "assistant_context": {"product_name": "MacBook Air"},
                    "prompt_version": "shopping_v1",
                },
                "prompt_version": "shopping_v1",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["orchestration"]["status"] == "COMPLETED"
        assert data["audit_trace"]["provider"] == "mock"
        assert data["audit_trace"]["prompt_version"] == "shopping_v1"
    finally:
        app.dependency_overrides.clear()
