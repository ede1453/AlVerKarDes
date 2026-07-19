from pathlib import Path

def test_rc448_password_reset_revokes_sessions_and_versions_tokens():
    text = Path(
        "app/domains/auth_core/service.py"
    ).read_text(encoding="utf-8")
    assert "PASSWORD_RECENTLY_USED" in text
    assert "security_version += 1" in text
    assert 'reason="password_reset"' in text
