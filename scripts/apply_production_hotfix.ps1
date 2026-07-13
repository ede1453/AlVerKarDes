$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

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

if (-not (Test-Path $EnvFile)) {
    throw "Missing $EnvFile"
}

Write-Host "Validating production environment..."
Invoke-NativeChecked `
    -Step "Production environment validation" `
    -Command {
        python .\scripts\check_production_env.py $EnvFile
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

$ApiPort = [int]$EnvValues["AICI_API_PORT"]

Write-Host "Stopping previous AICI production stack..."
Invoke-NativeChecked `
    -Step "Docker Compose down" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            down --remove-orphans
    }

Write-Host "Validating Docker Compose..."
Invoke-NativeChecked `
    -Step "Docker Compose config" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            config
    }

Write-Host "Building API image without stale dependency cache..."
Invoke-NativeChecked `
    -Step "Docker API build" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            build --no-cache api
    }

Write-Host "Starting database and Redis..."
Invoke-NativeChecked `
    -Step "Database and Redis startup" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            up -d db redis
    }

Write-Host "Checking asyncpg inside API image..."
Invoke-NativeChecked `
    -Step "asyncpg dependency check" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            run --rm api `
            python -c "import asyncpg; print('asyncpg dependency available')"
    }

Write-Host "Applying Alembic migrations..."
Invoke-NativeChecked `
    -Step "Alembic upgrade" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            run --rm api `
            alembic upgrade head
    }

Write-Host "Starting API on host port $ApiPort..."
Invoke-NativeChecked `
    -Step "API startup" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            up -d api
    }

Write-Host "Verifying production API container state..."
Invoke-NativeChecked `
    -Step "API container state check" `
    -Command {
        docker compose `
            --env-file $EnvFile `
            -f $ComposeFile `
            ps --status running api
    }

$ContainerId = docker compose `
    --env-file $EnvFile `
    -f $ComposeFile `
    ps -q api

if ($LASTEXITCODE -ne 0 -or -not $ContainerId) {
    throw "Production API container is not running."
}

$PortOwner = Get-NetTCPConnection `
    -LocalPort $ApiPort `
    -State Listen `
    -ErrorAction SilentlyContinue

if (-not $PortOwner) {
    throw "Nothing is listening on production API port $ApiPort."
}

Write-Host "Running smoke test against the isolated production port..."
Invoke-NativeChecked `
    -Step "Production smoke test" `
    -Command {
        python .\scripts\production_smoke_test.py `
            "http://127.0.0.1:$ApiPort"
    }

Write-Host "Production hotfix v1.3 validation passed."
