from app.domains.auth_core.password_policy import PasswordPolicy

def test_rc441_accepts_strong_password():
    result = PasswordPolicy().evaluate("Aici!Secure2026")
    assert result.valid is True
    assert result.score >= 60

def test_rc441_rejects_identity_fragment():
    result = PasswordPolicy().evaluate(
        "Ibrahim!Secure2026",
        identity_fragments=("ibrahim",),
    )
    assert "PASSWORD_CONTAINS_IDENTITY" in result.errors
