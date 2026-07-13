from pathlib import Path


def test_rc340_smoke_defaults_to_local_production_port():
    text = Path(
        "scripts/production_smoke_test.py"
    ).read_text(encoding="utf-8")

    assert "http://127.0.0.1:8000" in text
    assert '"base_url": BASE_URL' in text
