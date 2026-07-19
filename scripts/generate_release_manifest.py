from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

build_connector_readiness = importlib.import_module(
    "app.domains.commerce_ingestion.connector_readiness"
).build_connector_readiness

VERSION = "v1.0.0"
commit = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True, text=True, check=False
).stdout.strip() or "UNKNOWN"

digest = hashlib.sha256()
for path in sorted(
    [
        p
        for p in Path(".").rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and ".venv" not in p.parts
        and "__pycache__" not in p.parts
    ],
    key=lambda p: str(p),
):
    try:
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    except PermissionError:
        continue

connector_readiness = build_connector_readiness()
connector_readiness_snapshot = {
    "status": connector_readiness["status"],
    "summary": connector_readiness["summary"],
    "connectors": [
        {
            "connector_id": item["connector_id"],
            "mode": item["mode"],
            "operational_ready": item["operational_ready"],
            "production_ready": item["production_ready"],
            "missing_required_env": item["missing_required_env"],
        }
        for item in connector_readiness["connectors"]
    ],
}

manifest = {
    "version": VERSION,
    "commit_sha": commit,
    "source_digest_sha256": digest.hexdigest(),
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "release_status": "RELEASE_CANDIDATE_APPROVED",
    "production_port": 8000,
    "alembic_head": "0014_deal_storage_sqlalchemy",
    "connector_readiness": connector_readiness_snapshot,
}
Path("release").mkdir(exist_ok=True)
Path("release/release_manifest_v1.0.0.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(json.dumps(manifest, indent=2, ensure_ascii=False))



