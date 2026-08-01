param(
    [ValidateSet("backend", "frontend-unit", "frontend-e2e", "all")]
    [string]$Target = "backend",
    [string]$ComposeFile = "docker-compose.test.yml"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $composeArgs = @("-f", $ComposeFile)

    if ($Target -eq "all") {
        Write-Host "Running full compose CI workflow (all services)..." -ForegroundColor Cyan
        & docker compose @composeArgs up --abort-on-container-exit --exit-code-from backend
    }
    else {
        Write-Host "Running compose CI workflow for service '$Target'..." -ForegroundColor Cyan
        & docker compose @composeArgs run --rm $Target
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Compose CI workflow failed for target '$Target'."
    }

    Write-Host "Compose CI workflow passed for target '$Target'." -ForegroundColor Green
}
finally {
    Pop-Location
}
