$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$BaseUrl = "http://127.0.0.1:18000"

powershell -ExecutionPolicy Bypass -File .\scripts\wait_for_production_api.ps1
if ($LASTEXITCODE -ne 0) { throw "Production API health check failed." }

python .\scripts\production_smoke_test.py $BaseUrl
if ($LASTEXITCODE -ne 0) { throw "Production smoke test failed." }

python .\scripts\final_release_check.py $BaseUrl
if ($LASTEXITCODE -ne 0) { throw "Final release check returned NO_GO." }

python .\scripts\generate_release_manifest.py
if ($LASTEXITCODE -ne 0) { throw "Manifest generation failed." }

docker compose --env-file .\.env.production -f .\deploy\docker\docker-compose.production.yml run --rm api alembic current
if ($LASTEXITCODE -ne 0) { throw "Alembic current failed." }

docker compose --env-file .\.env.production -f .\deploy\docker\docker-compose.production.yml ps
if ($LASTEXITCODE -ne 0) { throw "Docker status check failed." }

Write-Host ""
Write-Host "FINAL RESULT: GO"
Write-Host "AI Consumer Intelligence v1.0.0 is approved for release."
