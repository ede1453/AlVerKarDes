import shutil
import zipfile
from pathlib import Path

from scripts.build_release_zip import build_release_zip
from scripts.check_release_hygiene import scan_zip

_RUNTIME_TMP = Path(__file__).resolve().parent / "runtime_tmp"


def _runtime_dir(name: str) -> Path:
    path = _RUNTIME_TMP / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_rc58_release_hygiene_detects_forbidden_zip_entries():
    workdir = _runtime_dir("rc58_bad_zip")
    bad_zip = workdir / "bad.zip"
    with zipfile.ZipFile(bad_zip, "w") as archive:
        archive.writestr("project/.env", "SECRET=1")
        archive.writestr("project/.venv/Lib/site-packages/example.py", "")
        archive.writestr("project/app/__pycache__/x.pyc", "")
        archive.writestr("project/.env.example", "EXAMPLE=1")

    findings = scan_zip(bad_zip)

    assert "project/.env" in findings
    assert "project/.venv/Lib/site-packages/example.py" in findings
    assert "project/app/__pycache__/x.pyc" in findings
    assert "project/.env.example" not in findings


def test_rc58_build_release_zip_excludes_local_runtime_files():
    workdir = _runtime_dir("rc58_release_zip")
    source = workdir / "source"
    source.mkdir()
    (source / "app").mkdir()
    (source / "app" / "main.py").write_text("print('ok')", encoding="utf-8")
    (source / ".env").write_text("SECRET=1", encoding="utf-8")
    (source / ".env.example").write_text("SECRET=", encoding="utf-8")
    (source / ".venv").mkdir()
    (source / ".venv" / "x.py").write_text("", encoding="utf-8")
    (source / "app" / "__pycache__").mkdir()
    (source / "app" / "__pycache__" / "main.pyc").write_text("", encoding="utf-8")

    output = workdir / "release.zip"
    build_release_zip(source, output)

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())

    assert "app/main.py" in names
    assert ".env.example" in names
    assert ".env" not in names
    assert ".venv/x.py" not in names
    assert "app/__pycache__/main.pyc" not in names