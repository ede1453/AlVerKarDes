from pathlib import Path


def test_rc340_hotfix_script_checks_native_exit_codes():
    text = Path(
        "scripts/apply_production_hotfix.ps1"
    ).read_text(encoding="utf-8")

    assert "Invoke-NativeChecked" in text
    assert "$LASTEXITCODE -ne 0" in text
    assert "build --no-cache api" in text
    assert "import asyncpg" in text
