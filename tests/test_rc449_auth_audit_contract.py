from pathlib import Path

def test_rc449_auth_audit_contains_security_context():
    text = Path(
        "app/domains/auth_core/models.py"
    ).read_text(encoding="utf-8")
    for field in (
        "event_type",
        "ip_address",
        "user_agent",
        "correlation_id",
        "occurred_at",
    ):
        assert field in text
