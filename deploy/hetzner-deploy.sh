#!/usr/bin/env bash
# LAUNCH-001: minimal Hetzner single-VPS deploy script -- DRAFT, NOT YET RUN
# against a real server (no Hetzner instance provisioned yet). This is a
# preparation artifact, not an applied deployment.
#
# Assumes: a single Hetzner VPS (no external managed DB/Redis -- this
# repo's own docker-compose.prod.yml Postgres/Redis containers ARE the
# database, per LAUNCH-000's finding that managed DB/Redis is still an
# open item, not yet decided). Run this AS the deploy user on the VPS
# itself, from the repo checkout at /opt/aici (matches
# deploy/systemd/aici-api.service's WorkingDirectory).
#
# What this script deliberately does NOT do:
# - Does not provision the VPS itself (firewall rules, Docker install --
#   see the checklist in ADR-020's LAUNCH-001 section for that).
# - Does not create/edit .env.prod -- that file holds real secrets and is
#   gitignored; it must be placed on the server out-of-band (e.g. `scp` a
#   pre-generated file, or a proper secret manager once LAUNCH-000's
#   secret-manager gap is closed). This script only checks it exists.
# - Does not touch TLS/nginx -- deploy/docker/docker-compose.production.yml's
#   `edge` profile (nginx + certs) is a separate, not-yet-decided step
#   (ADR-020, "önemli" priority #6).

set -euo pipefail

REPO_DIR="/opt/aici"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

cd "$REPO_DIR"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found in $REPO_DIR." >&2
    echo "Copy it from .env.prod.example, fill in real secrets (strong DB password," >&2
    echo "JWT_SECRET, INTERNAL_SERVICE_KEY -- see enforce_*_strength() guards in" >&2
    echo "app/main.py for the exact requirements), and place it here before deploying." >&2
    exit 1
fi

echo "==> Pulling latest code"
git fetch origin
git checkout "${1:-master}"
git pull origin "${1:-master}"

echo "==> Building and starting containers (Postgres/Redis/API)"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> Waiting for API health check"
for _ in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health > /dev/null; then
        echo "API is healthy."
        break
    fi
    sleep 2
done

echo "==> Running database migrations"
docker compose -f "$COMPOSE_FILE" exec -T aici-api alembic upgrade head

echo "==> Final readiness check"
curl -sf http://127.0.0.1:8000/ready || {
    echo "WARNING: /ready did not report healthy. Check 'docker compose -f $COMPOSE_FILE logs aici-api'." >&2
    exit 1
}

echo "==> Deploy complete."
