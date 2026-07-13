from pathlib import Path


def test_rc301_rc340_deployment_files_exist():
    required = [
        "deploy/docker/Dockerfile.production",
        "deploy/docker/docker-compose.production.yml",
        "deploy/nginx/aici.conf",
        "deploy/systemd/aici-api.service",
        "config/production.env.example",
        "scripts/production_smoke_test.py",
        "scripts/backup_postgres.ps1",
        "scripts/restore_postgres.ps1",
    ]

    for item in required:
        assert Path(item).exists(), item
