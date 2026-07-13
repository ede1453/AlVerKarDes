from pathlib import Path


def test_final_release_powershell_scripts_avoid_parenthesized_string_concat():
    for item in [
        "scripts/create_release_tag.ps1",
        "scripts/final_release_validation.ps1",
    ]:
        text = Path(item).read_text(encoding="utf-8")

        assert '+ "' not in text
        assert 'throw (' not in text
        assert 'Write-Host (' not in text


def test_powershell_syntax_validator_exists():
    assert Path(
        "scripts/validate_powershell_syntax.ps1"
    ).exists()
