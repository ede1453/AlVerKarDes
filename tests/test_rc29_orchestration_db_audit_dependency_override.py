from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover
    get_db = None

from app.domains.identity.dependencies import get_current_user
from app.domains.identity.models import UserRole


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

    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
        if "/api/v1/llm-orchestration/run-with-db-audit" not in paths:
            return

        # Auth registration/login must happen against the real DB, before
        # get_db is swapped out below for the fake in-memory one used to
        # prove this endpoint works without real Postgres.
        headers = auth_headers(client)

        app.dependency_overrides[get_db] = override_get_db
        # get_current_user also depends on get_db (to look the user back up
        # by id), which would otherwise hit FakeAsyncDB and break — it
        # doesn't support the ORM-style scalar_one_or_none() lookups
        # UserRepository needs. Override it directly so the guard on this
        # endpoint is satisfied without a real user lookup.
        # AUTH-006 Part 3: this endpoint also runs require_role(OPERATOR) on
        # top of get_current_user, so the stand-in needs a real `.role`
        # attribute at OPERATOR or above or the role check itself raises.
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="dependency-override-user", role=UserRole.OPERATOR
        )

        try:
            response = client.post(
                "/api/v1/llm-orchestration/run-with-db-audit",
                headers=headers,
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
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["audit_trace"]["provider"] == "mock"
    assert data["audit_trace"]["prompt_version"] == "shopping_v1"
