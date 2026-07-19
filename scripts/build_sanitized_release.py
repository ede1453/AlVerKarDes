from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import argparse
import hashlib
import json

from app.core.production_hardening import (
    path_is_release_safe,
    sha256_file,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="dist/aici_backend_sanitized.zip",
    )
    args = parser.parse_args()

    root = Path(".").resolve()
    output = Path(args.output).resolve()
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if path == output:
            continue

        if not path_is_release_safe(str(relative)):
            continue

        files.append((path, relative))

    with ZipFile(
        output,
        "w",
        ZIP_DEFLATED,
    ) as archive:
        for path, relative in files:
            archive.write(
                path,
                relative,
            )

    manifest = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "file_count": len(files),
        "archive": str(output),
        "sha256": sha256_file(output),
        "excluded_secret_files": True,
        "excluded_vcs_and_virtualenv": True,
    }

    manifest_path = output.with_suffix(
        ".manifest.json"
    )
    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
