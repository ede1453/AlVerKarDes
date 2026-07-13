from __future__ import annotations
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v1.0.0"
commit = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True, text=True, check=False
).stdout.strip() or "UNKNOWN"

digest = hashlib.sha256()
for path in sorted(
    [p for p in Path(".").rglob("*") if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts and "__pycache__" not in p.parts],
    key=lambda p: str(p),
):
    digest.update(str(path).encode())
    digest.update(path.read_bytes())

manifest = {
    "version": VERSION,
    "commit_sha": commit,
    "source_digest_sha256": digest.hexdigest(),
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "release_status": "RELEASE_CANDIDATE_APPROVED",
    "production_port": 18000,
    "alembic_head": "0014_deal_storage_sqlalchemy",
}
Path("release").mkdir(exist_ok=True)
Path("release/release_manifest_v1.0.0.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(json.dumps(manifest, indent=2, ensure_ascii=False))
