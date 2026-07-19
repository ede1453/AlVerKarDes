from app.core.production_hardening import archive_exclusion_patterns, path_is_release_safe


def test_arsiv_is_excluded():
    # Regression test for the actual leak found: a real generated release ZIP
    # included all 158 files from _arsiv/ (archived RC scripts, release
    # manifests, env backups) because this directory didn't exist when the
    # exclusion list was first written.
    assert path_is_release_safe("_arsiv/rc-scripts/run_rc1_final_validation.ps1") is False
    assert path_is_release_safe("_arsiv/misc/openapi.json") is False


def test_claude_config_is_excluded():
    # Same story: .claude/settings.local.json (local tooling config, not part
    # of the deployable app) leaked into a real generated ZIP.
    assert path_is_release_safe(".claude/settings.local.json") is False


def test_runtime_tmp_is_excluded():
    # Third real leak found via check_release_hygiene.py run against the
    # real ZIP: tests/runtime_tmp/ (leftover fixture state from previous
    # test runs) was already gitignored/dockerignored/pytest-excluded
    # everywhere else, but path_is_release_safe() never had it.
    assert path_is_release_safe("tests/runtime_tmp/openapi_snapshot_v1.json") is False
    assert path_is_release_safe("tests/runtime_tmp/rc58_release_zip/source/app/main.py") is False


def test_exclusion_patterns_list_documents_all_three():
    patterns = archive_exclusion_patterns()
    assert "_arsiv/" in patterns
    assert ".claude/" in patterns
    assert "tests/runtime_tmp/" in patterns


def test_still_excludes_original_categories():
    # Regression guard: the original finding (real secrets/.git/.venv leaking)
    # must stay fixed.
    assert path_is_release_safe(".env") is False
    assert path_is_release_safe(".git/config") is False
    assert path_is_release_safe(".venv/lib/site-packages/foo.py") is False
    assert path_is_release_safe("app/__pycache__/main.cpython-313.pyc") is False


def test_example_env_files_still_allowed():
    assert path_is_release_safe(".env.example") is True
    assert path_is_release_safe(".env.prod.example") is True


def test_app_source_still_included():
    assert path_is_release_safe("app/main.py") is True
    assert path_is_release_safe("requirements.txt") is True
