param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$ComposeFile = ".\deploy\docker\docker-compose.production.yml"
)

$ErrorActionPreference = "Stop"

Get-Content -Encoding Byte $BackupFile `
    | docker compose -f $ComposeFile exec -T db `
        pg_restore -U $env:POSTGRES_USER -d $env:POSTGRES_DB --clean --if-exists

Write-Host "Restore completed."
