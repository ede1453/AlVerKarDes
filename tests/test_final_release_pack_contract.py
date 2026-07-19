from pathlib import Path


def test_final_release_pack_scripts_exist():
    for item in [
        "scripts/final_release_check.py",
        "scripts/generate_release_manifest.py",
        "scripts/create_release_tag.ps1",
        "scripts/final_release_validation.ps1",
        "scripts/validate_release_manifest.py",
    ]:
        assert Path(item).exists(), item

def test_final_release_version_is_v1_0_0():
    text = Path("scripts/generate_release_manifest.py").read_text(encoding="utf-8")
    assert 'VERSION = "v1.0.0"' in text

def test_final_release_check_includes_connector_readiness_gate():
    text = Path("scripts/final_release_check.py").read_text(encoding="utf-8")

    assert "/api/v1/connector-operations/readiness" in text
    assert "connector_readiness" in text
    assert "ACTION_REQUIRED" in text

def test_release_manifest_includes_connector_readiness_snapshot():
    text = Path("scripts/generate_release_manifest.py").read_text(encoding="utf-8")

    assert "build_connector_readiness" in text
    assert "connector_readiness" in text
    assert "missing_required_env" in text

def test_final_release_check_runs_release_manifest_validation():
    text = Path("scripts/final_release_check.py").read_text(encoding="utf-8")

    assert "scripts/validate_release_manifest.py" in text
    assert "release_manifest" in text

def test_final_release_validation_uses_production_port_8000():
    text = Path("scripts/final_release_validation.ps1").read_text(encoding="utf-8")

    assert "http://127.0.0.1:8000" in text
    assert "http://127.0.0.1:18000" not in text


def test_final_release_validation_runs_manifest_validation_after_generation():
    text = Path("scripts/final_release_validation.ps1").read_text(encoding="utf-8")

    assert "Generating release manifest" in text
    assert "Validating release manifest" in text
    assert "python .\\scripts\\validate_release_manifest.py" in text

