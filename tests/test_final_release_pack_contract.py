from pathlib import Path

def test_final_release_pack_scripts_exist():
    for item in [
        "scripts/final_release_check.py",
        "scripts/generate_release_manifest.py",
        "scripts/create_release_tag.ps1",
        "scripts/final_release_validation.ps1",
    ]:
        assert Path(item).exists(), item

def test_final_release_version_is_v1_0_0():
    text = Path("scripts/generate_release_manifest.py").read_text(encoding="utf-8")
    assert 'VERSION = "v1.0.0"' in text
