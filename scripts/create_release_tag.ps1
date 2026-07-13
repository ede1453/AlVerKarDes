param([string]$Version = "v1.0.0")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
git status --short
if ($LASTEXITCODE -ne 0) { throw "Git repository check failed." }
if (git status --porcelain) { throw "Working tree is not clean." }
git tag -a $Version -m "AI Consumer Intelligence $Version production release"
if ($LASTEXITCODE -ne 0) { throw "Git tag creation failed." }
Write-Host "Created release tag: $Version"
Write-Host "Push with: git push origin $Version"
