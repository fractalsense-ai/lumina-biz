param(
    [string]$PythonExe = ".\\.venv\\Scripts\\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

& $PythonExe "scripts/single_box_readiness_check.py" `
    --health-report "data/staging/single-box-health-report.json" `
    --backups-dir "data/staging/backups" `
    --json-out "data/staging/single-box-readiness-report.json"

if ($LASTEXITCODE -ne 0) {
    throw "single_box_readiness_check.py failed with exit code $LASTEXITCODE"
}
