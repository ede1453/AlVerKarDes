from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

FORBIDDEN_PARTS = {
    ".venv",
    "venv",
    ".pytest_cache",
    ".pytest_tmp",
    "pytest_tmp",
    "runtime_tmp",
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".ruff_cache",
}

FORBIDDEN_FILENAMES = {
    ".env",
}

ALLOWED_ENV_EXAMPLES = {
    ".env.example",
    ".env.prod.example",
}


def _is_forbidden(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]

    if any(part in FORBIDDEN_PARTS for part in parts):
        return True

    name = parts[-1] if parts else ""
    if name in ALLOWED_ENV_EXAMPLES:
        return False

    if name in FORBIDDEN_FILENAMES:
        return True

    if name.endswith(".pyc") or name.endswith(".pyo"):
        return True

    return False


def scan_zip(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return sorted(name for name in archive.namelist() if _is_forbidden(name))


def scan_folder(path: Path) -> list[str]:
    findings = []
    for item in path.rglob("*"):
        rel = item.relative_to(path).as_posix()
        if _is_forbidden(rel):
            findings.append(rel)
    return sorted(findings)


def scan(path: Path) -> list[str]:
    if path.is_file() and path.suffix.lower() == ".zip":
        return scan_zip(path)
    if path.is_dir():
        return scan_folder(path)
    raise FileNotFoundError(f"Path not found or unsupported: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release artifacts for forbidden local/runtime files.")
    parser.add_argument("path", help="ZIP file or folder to scan")
    args = parser.parse_args()

    path = Path(args.path)
    findings = scan(path)

    if findings:
        print("Release hygiene check failed. Forbidden entries:")
        for finding in findings[:200]:
            print(f"- {finding}")
        if len(findings) > 200:
            print(f"... and {len(findings) - 200} more")
        return 1

    print("Release hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())