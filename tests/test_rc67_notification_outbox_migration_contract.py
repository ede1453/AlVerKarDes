from pathlib import Path


def test_rc67_notification_outbox_migration_file_exists():
    path = Path("alembic/versions/0011_notification_outbox.py")

    assert path.exists()


def test_rc67_notification_outbox_migration_defines_expected_table_and_columns():
    content = Path("alembic/versions/0011_notification_outbox.py").read_text(encoding="utf-8")

    assert "notification_outbox" in content
    assert "user_id" in content
    assert "channel" in content
    assert "status" in content
    assert "retry_count" in content
    assert "next_retry_at" in content
    assert "last_error" in content
    assert "idempotency_key" in content
