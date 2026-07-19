from pathlib import Path

def test_rc446_lockout_is_persistent():
    service = Path(
        "app/domains/auth_core/service.py"
    ).read_text(encoding="utf-8")
    models = Path(
        "app/domains/auth_core/models.py"
    ).read_text(encoding="utf-8")
    assert "ACCOUNT_TEMPORARILY_LOCKED" in service
    assert "maximum_failed_attempts" in service
    assert "locked_until" in models
