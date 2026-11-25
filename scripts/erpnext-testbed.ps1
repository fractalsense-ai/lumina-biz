[CmdletBinding()]
param(
    [ValidateSet("up", "status", "logs", "down")]
    [string]$Action = "up",
    [ValidateRange(1, 65535)]
    [int]$Port = 18080
)

$ErrorActionPreference = "Stop"

$projectName = "lumina-erpnext-test"
$composeRevision = "48b9479a9697d0049e795fd7b682eb6544923410"
$baseCompose = Join-Path $env:TEMP "lumina-erpnext-pwd-$composeRevision.yml"
$overrideCompose = Join-Path $PSScriptRoot "..\testbed\erpnext-compose.override.yml"
$composeArgs = @(
    "compose",
    "--project-name", $projectName,
    "-f", $baseCompose,
    "-f", $overrideCompose
)

if (-not (Test-Path $baseCompose)) {
    $composeUrl = "https://raw.githubusercontent.com/frappe/frappe_docker/$composeRevision/pwd.yml"
    Invoke-WebRequest -Uri $composeUrl -OutFile $baseCompose
}

$env:LUMINA_ERP_TESTBED_PORT = [string]$Port

switch ($Action) {
    "up" {
        $runningFrontend = & docker @composeArgs ps --status running --quiet frontend
        if (-not $runningFrontend) {
            $portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
            if ($portInUse) {
                throw "Port $Port is already listening. Choose another port with -Port."
            }
        }

        & docker @composeArgs config --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "The ERPNext test-bed Compose configuration is invalid."
        }

        & docker @composeArgs up -d
        if ($LASTEXITCODE -ne 0) {
            throw "ERPNext test-bed startup failed."
        }

        $siteContainer = (& docker @composeArgs ps --all --quiet create-site | Select-Object -First 1)
        if (-not $siteContainer) {
            throw "ERPNext site initialization container was not found."
        }
        $siteExitCode = (& docker wait $siteContainer).Trim()
        if ($LASTEXITCODE -ne 0) {
            throw "Could not wait for ERPNext site initialization."
        }
        if ($siteExitCode -ne "0") {
            throw "ERPNext site initialization exited with code $siteExitCode. Run the status action for logs."
        }

        $adminPassword = [Guid]::NewGuid().ToString("N")
        & docker @composeArgs exec --no-TTY backend bench --site frontend set-admin-password $adminPassword
        if ($LASTEXITCODE -ne 0) {
            throw "Could not set a private local Administrator password."
        }

        $passwordFile = Join-Path $env:TEMP "lumina-erpnext-testbed-admin-password.txt"
        [System.IO.File]::WriteAllText($passwordFile, $adminPassword)
        Write-Output "ERPNext is available at http://127.0.0.1:$Port"
        Write-Output "Login: Administrator; password stored in $passwordFile"
        Write-Output "Use site name 'frontend' for API requests. This disposable stack uses its own Compose volumes."
    }
    "status" {
        & docker @composeArgs ps --all
        if ($LASTEXITCODE -ne 0) {
            throw "Could not read ERPNext test-bed status."
        }
    }
    "logs" {
        & docker @composeArgs logs --tail 80 create-site
        if ($LASTEXITCODE -ne 0) {
            throw "Could not read ERPNext site initialization logs."
        }
    }
    "down" {
        & docker @composeArgs down --volumes --remove-orphans
        if ($LASTEXITCODE -ne 0) {
            throw "Could not remove the isolated ERPNext test-bed."
        }
    }
}