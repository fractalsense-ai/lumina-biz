[CmdletBinding()]
param(
    [ValidateSet("up", "status", "down")]
    [string]$Action = "status",
    [ValidateSet("lumen", "ury")]
    [string]$Candidate = "lumen",
    [ValidateRange(1, 65535)]
    [int]$Port = 18081
)

$ErrorActionPreference = "Stop"
if ($Candidate -eq "ury" -and -not $PSBoundParameters.ContainsKey("Port")) { $Port = 18082 }
$project = "lumina-$Candidate-eval"
$revision = "48b9479a9697d0049e795fd7b682eb6544923410"
$base = Join-Path $env:TEMP "lumina-erpnext-pwd-$revision.yml"
$overlay = Join-Path $PSScriptRoot "lumen-restaurants.override.yml"
$secrets = Join-Path $env:TEMP "lumina-$Candidate-evaluation-secrets.json"
$composeArgs = @("compose", "--project-name", $project, "-f", $base, "-f", $overlay)
if ($Candidate -eq "ury") {
    $composeArgs += @("-f", (Join-Path $PSScriptRoot "ury-evaluation.override.yml"))
}

if (-not (Test-Path $base)) {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/frappe/frappe_docker/$revision/pwd.yml" -OutFile $base
}

if ($Action -eq "up" -and -not (Test-Path $secrets)) {
    $existingContainers = & docker ps -aq --filter "label=com.docker.compose.project=$project"
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect existing evaluation containers." }
    $existingVolumes = & docker volume ls -q --filter "label=com.docker.compose.project=$project"
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect existing evaluation volumes." }
    if ($existingContainers -or $existingVolumes) { throw "Existing evaluation data found without credentials; refusing to overwrite it." }
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is already listening; choose a different port."
    }
    $generated = @{
        database = [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")
        administrator = [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")
    }
    [System.IO.File]::WriteAllText($secrets, ($generated | ConvertTo-Json))
}

if (Test-Path $secrets) {
    $values = Get-Content -Raw $secrets | ConvertFrom-Json
} elseif ($Action -eq "up") {
    throw "Evaluation credentials not found; run with -Action up first."
} else {
    $values = @{ database = "unused-for-read-or-cleanup"; administrator = "unused-for-read-or-cleanup" }
}
$env:LUMEN_EVAL_DB_PASSWORD = $values.database
$env:LUMEN_EVAL_ADMIN_PASSWORD = $values.administrator
$env:LUMEN_EVAL_PORT = [string]$Port

try {
    if ($Action -eq "up") {
        & docker @composeArgs config --quiet
        if ($LASTEXITCODE -ne 0) { throw "Evaluation Compose configuration is invalid." }
        & docker @composeArgs up -d
        if ($LASTEXITCODE -ne 0) { throw "Evaluation stack startup failed." }
        $initializer = & docker @composeArgs ps --all --quiet create-site
        if ($LASTEXITCODE -ne 0 -or -not $initializer) { throw "Evaluation initializer not found." }
        $result = (& docker wait $initializer).Trim()
        if ($LASTEXITCODE -ne 0 -or $result -ne "0") { throw "Evaluation site initialization failed; inspect create-site logs." }
        Write-Output "Evaluation URL: http://127.0.0.1:$Port"
        Write-Output "Administrator credentials: $secrets"
    } else {
        if ($Action -eq "status") {
            & docker @composeArgs ps --all
            if ($LASTEXITCODE -ne 0) { throw "Could not inspect evaluation stack." }
        } else {
            & docker @composeArgs down --volumes --remove-orphans
            if ($LASTEXITCODE -ne 0) { throw "Could not remove the isolated evaluation stack." }
            Remove-Item $secrets -Force -ErrorAction SilentlyContinue
            Write-Output "Removed only the lumina-$Candidate-eval project, its volumes, and its temporary credentials."
        }
    }
} finally {
    Remove-Item Env:LUMEN_EVAL_DB_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:LUMEN_EVAL_ADMIN_PASSWORD -ErrorAction SilentlyContinue
}