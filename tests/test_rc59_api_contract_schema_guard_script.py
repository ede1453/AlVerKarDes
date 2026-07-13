from pathlib import Path


def test_rc59_schema_guard_script_exists():
    assert Path("scripts/api_contract_schema_guard.py").exists()


def test_rc59_schema_guard_script_has_cli_success_message():
    content = Path("scripts/api_contract_schema_guard.py").read_text(encoding="utf-8")

    assert "API schema contract guard passed." in content
    assert "REQUEST_BODY_SCHEMA_CHANGED" in content
    assert "RESPONSE_SCHEMA_CHANGED" in content
