from pathlib import Path


def test_rc340_smoke_script_has_local_default_and_placeholder_guard():
    text = Path(
        "scripts/production_smoke_test.py"
    ).read_text(encoding="utf-8")

    assert "http://127.0.0.1:8000" in text
    assert "YOUR_DOMAIN" in text
