from pathlib import Path


def test_local_validation_runner_exists():
    path = Path("run_local_validation.ps1")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "python -m pytest -q" in content
    assert "/api/v1/integrity/check" in content
    assert "/api/v1/system/release-health" in content
