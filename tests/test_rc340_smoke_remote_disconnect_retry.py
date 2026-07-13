from pathlib import Path


def test_rc340_smoke_retries_remote_disconnect():
    text = Path(
        "scripts/production_smoke_test.py"
    ).read_text(encoding="utf-8")

    assert "http.client.RemoteDisconnected" in text
    assert "MAX_ATTEMPTS = 60" in text
    assert "ConnectionResetError" in text
