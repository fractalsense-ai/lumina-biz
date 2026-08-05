param(
    [ValidateSet("backup", "restore", "prune")]
    [string]$Action = "backup",
    [string]$PythonExe = ".\\.venv\\Scripts\\python.exe",
    [string]$Archive = "",
    [int]$Keep = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$args = @("scripts/single_box_backup_restore.py", $Action)

if ($Action -eq "restore") {
    if ([string]::IsNullOrWhiteSpace($Archive)) {
        throw "-Archive is required when Action=restore"
    }
    $args += @("--archive", $Archive)
    if ($DryRun) {
        $args += "--dry-run"
    }
}

if ($Action -eq "prune") {
    $args += @("--keep", "$Keep")
}

if ($Action -eq "backup") {
    $args += @("--retention-limit", "$Keep")
}

& $PythonExe @args
