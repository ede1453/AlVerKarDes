from pathlib import Path

required = [
    "deploy/docker/Dockerfile.production",
    "deploy/docker/docker-compose.production.yml",
    "deploy/nginx/aici.conf",
    "deploy/systemd/aici-api.service",
    "config/production.env.example",
    "scripts/production_smoke_test.py",
    "scripts/check_production_env.py",
]

missing = [item for item in required if not Path(item).exists()]

if missing:
    raise SystemExit(f"Missing release artifacts: {missing}")

print("Release artifact check passed.")
