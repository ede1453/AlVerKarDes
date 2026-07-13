from __future__ import annotations
import json, subprocess, sys, urllib.request
from pathlib import Path

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:18000"
REQUIRED_FILES = [
    "deploy/docker/Dockerfile.production",
    "deploy/docker/docker-compose.production.yml",
    "config/production.env.example",
    "scripts/production_smoke_test.py",
    "scripts/check_production_env.py",
    "scripts/ensure_alembic_version_capacity.sql",
]
results = {"base_url": BASE_URL, "checks": {}}
missing = [x for x in REQUIRED_FILES if not Path(x).exists()]
results["checks"]["required_files"] = {"passed": not missing, "missing": missing}

for path in ["/health", "/openapi.json"]:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=15) as response:
            passed, status = response.status == 200, response.status
    except Exception as exc:
        passed, status = False, str(exc)
    results["checks"][f"http:{path}"] = {"passed": passed, "status": status}

def run(cmd):
    c = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return c.returncode == 0, (c.stdout + c.stderr).strip()

ok, out = run(["python", "-m", "pytest", "-q"])
results["checks"]["pytest"] = {"passed": ok, "output_tail": out[-3000:]}
ok, out = run(["python", "scripts/check_openapi_uniqueness.py"])
results["checks"]["openapi_uniqueness"] = {"passed": ok, "output": out}

all_passed = all(v.get("passed") for v in results["checks"].values())
results["go_no_go"] = "GO" if all_passed else "NO_GO"
Path("release").mkdir(exist_ok=True)
Path("release/final_release_check.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(json.dumps(results, indent=2, ensure_ascii=False))
if not all_passed:
    raise SystemExit(1)
