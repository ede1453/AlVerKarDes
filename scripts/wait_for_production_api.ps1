param(
    [string]$ComposeFile = ".\deploy\docker\docker-compose.production.yml",
    [string]$EnvFile = ".\.env.production",
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$elapsed = 0

while ($elapsed -lt $TimeoutSeconds) {
    $containerId = docker compose `
        --env-file $EnvFile `
        -f $ComposeFile `
        ps -q api

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to query API container."
    }

    if ($containerId) {
        $state = docker inspect `
            --format "{{.State.Status}}" `
            $containerId

        $health = docker inspect `
            --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" `
            $containerId

        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect API container."
        }

        Write-Host "API state=$state health=$health elapsed=${elapsed}s"

        if ($state -eq "exited" -or $state -eq "dead") {
            docker compose `
                --env-file $EnvFile `
                -f $ComposeFile `
                logs --no-color --tail=200 api

            throw "Production API container stopped during startup."
        }

        if ($state -eq "running" -and ($health -eq "healthy" -or $health -eq "none")) {
            Write-Host "Production API container is ready."
            exit 0
        }
    }

    Start-Sleep -Seconds 2
    $elapsed += 2
}

docker compose `
    --env-file $EnvFile `
    -f $ComposeFile `
    logs --no-color --tail=200 api

throw "Production API did not become healthy within $TimeoutSeconds seconds."
