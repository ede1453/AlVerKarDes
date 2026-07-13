from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    ".pytest_tmp",
    "pytest_tmp",
    "runtime_tmp",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}

EXCLUDED_FILES = {
    ".env",
}

ALLOWED_ENV_EXAMPLES = {
    ".env.example",
    ".env.prod.example",
}


def should_exclude(path: Path, source: Path) -> bool:
    rel_parts = path.relative_to(source).parts

    if any(part in EXCLUDED_DIRS for part in rel_parts):
        return True

    name = path.name
    if name in ALLOWED_ENV_EXAMPLES:
        return False

    if name in EXCLUDED_FILES:
        return True

    if name.endswith((".pyc", ".pyo", ".zip", ".log")):
        return True

    return False


def build_release_zip(source: Path, output: Path) -> None:
    source = source.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in source.rglob("*"):
            if item == output or should_exclude(item, source):
                continue
            if item.is_file():
                archive.write(item, item.relative_to(source).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a clean release ZIP from the current backend source tree.")
    parser.add_argument("--source", default=".", help="Source folder. Default: current folder")
    parser.add_argument("--output", required=True, help="Output ZIP path")
    args = parser.parse_args()

    build_release_zip(Path(args.source), Path(args.output))
    print(f"Release ZIP created: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())