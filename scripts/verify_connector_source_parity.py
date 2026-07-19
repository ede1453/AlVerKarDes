from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

compose_file = sys.argv[1] if len(sys.argv) > 1 else r".\deploy\docker\docker-compose.production.yml"
env_file = sys.argv[2] if len(sys.argv) > 2 else r".\.env.production"
local_file = Path("app/api/v1/marketplace_connectors_router.py")
local_hash = hashlib.sha256(local_file.read_bytes()).hexdigest()

command = [
    "docker","compose","--env-file",env_file,"-f",compose_file,
    "exec","-T","api","python","-c",
    "from pathlib import Path; import hashlib,json; p=Path('/app/app/api/v1/marketplace_connectors_router.py'); b=p.read_bytes(); print(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'has_ebay_health':'/ebay/health' in b.decode(),'has_idealo_health':'/idealo/health' in b.decode()}))"
]
completed = subprocess.run(command, capture_output=True, text=True, check=False)
if completed.returncode != 0:
    raise SystemExit(completed.stderr or completed.stdout)

container_data = json.loads(completed.stdout.strip().splitlines()[-1])
result = {"local_sha256": local_hash, "container": container_data, "matching": local_hash == container_data["sha256"]}
print(json.dumps(result, indent=2, ensure_ascii=False))

if not result["matching"]:
    raise SystemExit("Production container source differs from local source.")
if not container_data["has_ebay_health"]:
    raise SystemExit("Container router does not contain eBay health route.")
if not container_data["has_idealo_health"]:
    raise SystemExit("Container router does not contain Idealo health route.")
print("Connector source parity check passed.")
