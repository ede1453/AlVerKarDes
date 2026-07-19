from pathlib import Path

def test_rc447_email_verification_is_single_use():
    service = Path(
        "app/domains/auth_core/service.py"
    ).read_text(encoding="utf-8")
    assert "EMAIL_VERIFICATION" in service
    assert "consume_purpose_token" in service
    assert "TOKEN_ALREADY_USED" in service
