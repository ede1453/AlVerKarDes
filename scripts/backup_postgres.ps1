param(
    [string]$ComposeFile = ".\deploy\docker\docker-compose.production.yml",
    [string]$OutputDirectory = ".\backups"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$output = Join-Path $OutputDirectory "aici-$timestamp.dump"

docker compose -f $ComposeFile exec -T db `
    pg_dump -U $env:POSTGRES_USER -d $env:POSTGRES_DB -Fc `
    | Set-Content -Encoding Byte $output

Write-Host "Backup created: $output"
