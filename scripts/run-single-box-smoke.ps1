param(
    [string]$PythonExe = ".\\.venv\\Scripts\\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

& $PythonExe "scripts/single_box_health_check.py" `
    --runtime-config "model-packs/business-ops/cfg/runtime-config.yaml" `
    --json-out "data/staging/single-box-health-report.json" `
    --fail-on-degraded
