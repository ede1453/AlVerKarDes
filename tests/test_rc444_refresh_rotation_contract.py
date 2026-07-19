from pathlib import Path

def test_rc444_rotation_has_reuse_detection():
    text = Path(
        "app/domains/auth_core/service.py"
    ).read_text(encoding="utf-8")
    assert "REFRESH_TOKEN_REUSE_DETECTED" in text
    assert "revoke_token_family" in text
    assert "COMPROMISED" in text
