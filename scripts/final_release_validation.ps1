$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$BaseUrl = "http://127.0.0.1:8000"
$ComposeFile = ".\deploy\docker\docker-compose.production.yml"
$EnvFile = ".\.env.production"

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Step
    )

    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

if (-not $env:VIRTUAL_ENV) {
    throw "No active Python virtual environment detected. Activate .venv before running final release validation."
}

Write-Host "Active virtualenv: $env:VIRTUAL_ENV"

Write-Host "1/8 Waiting for production API health..."
Invoke-NativeChecked `
    -Step "Production API health check" `
    -Command {
        powershell -ExecutionPolicy Bypass `
            -File .\scripts\wait_for_production_api.ps1 `
            -ComposeFile $ComposeFile `
            -EnvFile $EnvFile
    }

Write-Host "2/8 Running production smoke tests..."
Invoke-NativeChecked `
    -Step "Production smoke test" `
    -Command {
        python .\scripts\production_smoke_test.py $BaseUrl
    }

Write-Host "3/8 Running host test suite and production runtime checks..."
Invoke-NativeChecked `
    -Step "Final release check" `
    -Command {
        python .\scripts\final_release_check.py `
            $BaseUrl `
            $ComposeFile `
            $EnvFile
    }

Write-Host "4/8 Generating release manifest..."
Invoke-NativeChecked `
    -Step "Release manifest generation" `
    -Command {
        python .\scripts\generate_release_manifest.py
    }

Write-Host "5/8 Validating release manifest..."
Invoke-NativeChecked `
    -Step "Release manifest validation" `
    -Command {
        python .\scripts\validate_release_manifest.py
    }

Write-Host "6/8 Confirming Alembic head..."
Invoke-NativeChecked `
    -Step "Alembic current" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            run --rm api alembic current
    }

Write-Host "7/8 Displaying production containers..."
Invoke-NativeChecked `
    -Step "Docker Compose status" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            ps
    }

Write-Host "8/8 Checking generated release reports..."

$requiredReports = @(
    ".\release\final_release_check.json",
    ".\release\release_manifest_v1.0.0.json"
)

foreach ($report in $requiredReports) {
    if (-not (Test-Path $report)) {
        throw "Missing release report: $report"
    }
}

Write-Host ""
Write-Host "FINAL RESULT: GO"
Write-Host "AI Consumer Intelligence v1.0.0 is approved as a local production release candidate."

