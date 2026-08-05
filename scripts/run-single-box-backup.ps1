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

$cmdArgs = @("scripts/single_box_backup_restore.py", $Action)

if ($Action -eq "restore") {
    if ([string]::IsNullOrWhiteSpace($Archive)) {
        throw "-Archive is required when Action=restore"
    }
    $cmdArgs += @("--archive", $Archive)
    if ($DryRun) {
        $cmdArgs += "--dry-run"
    }
}

if ($Action -eq "prune") {
    $cmdArgs += @("--keep", "$Keep")
}

if ($Action -eq "backup") {
    $cmdArgs += @("--retention-limit", "$Keep")
}

& $PythonExe @cmdArgs
