# RC1 Release Checklist

## Required

```powershell
python -m pytest -q
powershell -ExecutionPolicy Bypass -File .\run_local_validation.ps1
```

## Docker Production

```powershell
copy .env.prod.example .env.prod
notepad .env.prod
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec aici-api alembic upgrade head
```

## Smoke

```powershell
Invoke-RestMethod "http://localhost:8000/health" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://localhost:8000/api/v1/system/release-health" | ConvertTo-Json -Depth 12
```

## Pass Criteria

- tests pass
- local validation passes
- Docker API starts
- Alembic upgrade head succeeds
- release-health passed=true
