from app.core.runtime_settings import runtime_settings_status


def test_rc60_runtime_settings_status_does_not_expose_secret_names(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret")
    monkeypatch.setenv("AICI_ENVIRONMENT", "local")

    status = runtime_settings_status()
    text = str(status)

    assert "secret-value" not in text
    assert "postgresql://secret" not in text
    assert "OPENAI_API_KEY" not in text
    assert "DATABASE_URL" not in text
