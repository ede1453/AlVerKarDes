$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = ".\deploy\docker\docker-compose.production.yml"
$EnvFile = ".\.env.production"

function Invoke-NativeChecked {
    param([scriptblock]$Command,[string]$Step)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit code $LASTEXITCODE." }
}

Invoke-NativeChecked -Step "Remove API container" -Command {
    docker compose --env-file $EnvFile -f $ComposeFile rm -sf api
}

$imageId = docker images -q aici-production-api:latest
if ($imageId) {
    docker image rm -f $imageId
    if ($LASTEXITCODE -ne 0) { throw "Image removal failed." }
}

Invoke-NativeChecked -Step "Build API" -Command {
    docker compose --env-file $EnvFile -f $ComposeFile build --no-cache --pull api
}

Invoke-NativeChecked -Step "Start API" -Command {
    docker compose --env-file $EnvFile -f $ComposeFile up -d --force-recreate api
}

Invoke-NativeChecked -Step "Wait for API" -Command {
    powershell -ExecutionPolicy Bypass -File .\scripts\wait_for_production_api.ps1 -ComposeFile $ComposeFile -EnvFile $EnvFile
}

Invoke-NativeChecked -Step "Source parity" -Command {
    python .\scripts\verify_connector_source_parity.py $ComposeFile $EnvFile
}

Invoke-NativeChecked -Step "Container route inspection" -Command {
    docker compose --env-file $EnvFile -f $ComposeFile exec -T api python -c "from app.main import app; [print(r.path) for r in app.routes if 'marketplace-connectors' in r.path]"
}

Invoke-NativeChecked -Step "Marketplace list smoke test" -Command {
    python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/marketplace-connectors',timeout=10).status)"
}

Invoke-NativeChecked -Step "eBay health smoke test" -Command {
    python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/marketplace-connectors/ebay/health',timeout=10).status)"
}

Invoke-NativeChecked -Step "Idealo health smoke test" -Command {
    python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/marketplace-connectors/idealo/health',timeout=10).status)"
}

Write-Host "Clean connector API rebuild completed successfully."
