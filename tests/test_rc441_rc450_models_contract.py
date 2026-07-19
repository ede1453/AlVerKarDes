from app.domains.auth_core.models import (
    AccountSecurityState,
    AuthAuditEvent,
    AuthSession,
    AuthToken,
    LoginAttempt,
    PasswordHistory,
)

def test_rc441_rc450_table_names():
    assert AuthSession.__tablename__ == "auth_sessions"
    assert AuthToken.__tablename__ == "auth_tokens"
    assert LoginAttempt.__tablename__ == "auth_login_attempts"
    assert AccountSecurityState.__tablename__ == "auth_account_security"
    assert PasswordHistory.__tablename__ == "auth_password_history"
    assert AuthAuditEvent.__tablename__ == "auth_audit_events"
