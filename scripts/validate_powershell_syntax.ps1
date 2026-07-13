$ErrorActionPreference = "Stop"

$files = @(
    ".\scripts\create_release_tag.ps1",
    ".\scripts\final_release_validation.ps1"
)

foreach ($file in $files) {
    $errors = $null
    $tokens = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        (Resolve-Path $file),
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    if ($errors.Count -gt 0) {
        Write-Host "Syntax errors in $file"
        $errors | ForEach-Object {
            Write-Host $_.Message
        }
        exit 1
    }

    Write-Host "PowerShell syntax valid: $file"
}
