from pathlib import Path


def test_release_check_uses_host_venv_for_pytest():
    text = Path(
        "scripts/final_release_check.py"
    ).read_text(encoding="utf-8")

    assert '"host_active_virtualenv"' in text
    assert "sys.executable" in text
    assert '"-m",\n        "pytest"' in text


def test_release_check_uses_container_for_runtime_only():
    text = Path(
        "scripts/final_release_check.py"
    ).read_text(encoding="utf-8")

    assert "production_runtime_imports" in text
    assert "import asyncpg" in text
    assert "from app.main import app" in text


def test_tag_script_can_commit_current_changes_explicitly():
    text = Path(
        "scripts/create_release_tag.ps1"
    ).read_text(encoding="utf-8")

    assert "CommitCurrentChanges" in text
    assert "git add ." in text
    assert "git commit" in text
