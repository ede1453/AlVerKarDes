param(
    [string]$Version = "v1.0.0",
    [switch]$CommitCurrentChanges
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$insideGit = git rev-parse --is-inside-work-tree 2>$null

if ($LASTEXITCODE -ne 0 -or $insideGit -ne "true") {
    throw "This folder is not a Git repository. Run git init, configure user.name and user.email, add files, and create the first commit."
}

$changes = git status --porcelain

if ($LASTEXITCODE -ne 0) {
    throw "Git status check failed."
}

if ($changes) {
    if (-not $CommitCurrentChanges) {
        Write-Host "Working tree contains uncommitted changes:"
        git status --short
        throw "Commit the current changes first, or rerun with -CommitCurrentChanges."
    }

    git add .

    if ($LASTEXITCODE -ne 0) {
        throw "Git add failed."
    }

    git commit -m "Prepare AI Consumer Intelligence $Version release"

    if ($LASTEXITCODE -ne 0) {
        throw "Git commit failed. Configure git user.name and git user.email if necessary."
    }
}

$existingTag = git tag --list $Version

if ($LASTEXITCODE -ne 0) {
    throw "Git tag lookup failed."
}

if ($existingTag -eq $Version) {
    Write-Host "Release tag already exists: $Version"
    exit 0
}

git tag -a $Version -m "AI Consumer Intelligence $Version production release"

if ($LASTEXITCODE -ne 0) {
    throw "Git tag creation failed."
}

Write-Host "Created release tag: $Version"

$remotes = git remote

if ($LASTEXITCODE -ne 0) {
    throw "Git remote lookup failed."
}

if ($remotes) {
    Write-Host "Push tag with: git push origin $Version"
}
else {
    Write-Host "No Git remote is configured. The local release tag was created."
}
