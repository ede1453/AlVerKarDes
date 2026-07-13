$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = ".\deploy\docker\docker-compose.production.yml"
$EnvFile = ".\.env.production"
$SqlFile = ".\scripts\ensure_alembic_version_capacity.sql"

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

foreach ($RequiredFile in @($ComposeFile, $EnvFile, $SqlFile)) {
    if (-not (Test-Path $RequiredFile)) {
        throw "Missing required file: $RequiredFile"
    }
}

$EnvValues = @{}

Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()

    if (
        $line -and
        -not $line.StartsWith("#") -and
        $line.Contains("=")
    ) {
        $parts = $line.Split("=", 2)
        $EnvValues[$parts[0].Trim()] = $parts[1].Trim()
    }
}

$PostgresUser = $EnvValues["POSTGRES_USER"]
$PostgresDb = $EnvValues["POSTGRES_DB"]
$ApiPort = [int]$EnvValues["AICI_API_PORT"]

Write-Host "Starting PostgreSQL and Redis..."
Invoke-NativeChecked `
    -Step "Database startup" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            up -d db redis
    }

Write-Host "Expanding Alembic version column to VARCHAR(128)..."
$SqlText = Get-Content $SqlFile -Raw

$SqlText | docker compose `
    --env-file $EnvFile `
    -f $ComposeFile `
    exec -T db `
    psql `
    -v ON_ERROR_STOP=1 `
    -U $PostgresUser `
    -d $PostgresDb

if ($LASTEXITCODE -ne 0) {
    throw "Alembic version table repair failed with exit code $LASTEXITCODE."
}

Write-Host "Running Alembic migrations..."
Invoke-NativeChecked `
    -Step "Alembic upgrade" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            run --rm api `
            alembic upgrade head
    }

Write-Host "Starting production API..."
Invoke-NativeChecked `
    -Step "Production API startup" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            up -d api
    }

Write-Host "Waiting for production API health..."
powershell -ExecutionPolicy Bypass `
    -File .\scripts\wait_for_production_api.ps1 `
    -ComposeFile $ComposeFile `
    -EnvFile $EnvFile `
    -TimeoutSeconds 120

if ($LASTEXITCODE -ne 0) {
    throw "Production API health wait failed with exit code $LASTEXITCODE."
}

Write-Host "Running production smoke test on port $ApiPort..."
Invoke-NativeChecked `
    -Step "Production smoke test" `
    -Command {
        python .\scripts\production_smoke_test.py `
            "http://127.0.0.1:$ApiPort"
    }

Write-Host "Migration, API startup, health wait, and smoke test completed successfully."
