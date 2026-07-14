[CmdletBinding()]
param(
    [string]$DatabasePath = "01_data/db/smr.db",
    [int]$ApiPort = 3000,
    [int]$UiPort = 5173
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "local-common.ps1")

$ProjectRoot = Get-SmrProjectRoot
$databaseFullPath = Resolve-SmrPath -ProjectRoot $ProjectRoot -Path $DatabasePath
$failures = 0
$warnings = 0

function Write-Diagnostic {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("OK", "WARN", "FAIL")][string]$Level,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($Level -eq "WARN") { $script:warnings += 1 }
    if ($Level -eq "FAIL") { $script:failures += 1 }
    Write-Host "[$Level] $Message"
}

Write-Host "SMR local environment diagnostics"
Write-Host "Project: $ProjectRoot"

$python = $null
try {
    $python = Resolve-SmrPython -ProjectRoot $ProjectRoot
    $version = & $python.Executable @($python.Prefix) --version 2>&1
    Write-Diagnostic -Level "OK" -Message "Python is available: $version"
}
catch {
    Write-Diagnostic -Level "FAIL" -Message $_.Exception.Message
}

try {
    $node = Resolve-SmrNode
    $nodeVersion = & $node --version 2>&1
    Write-Diagnostic -Level "OK" -Message "Node.js is available: $nodeVersion"
}
catch {
    Write-Diagnostic -Level "FAIL" -Message $_.Exception.Message
}

$viteEntry = Join-Path $ProjectRoot "node_modules\vite\bin\vite.js"
if (Test-Path -LiteralPath $viteEntry -PathType Leaf) {
    Write-Diagnostic -Level "OK" -Message "Frontend dependencies are installed."
}
else {
    Write-Diagnostic -Level "FAIL" -Message "Frontend dependencies are missing. Run npm ci."
}

if (-not (Test-Path -LiteralPath $databaseFullPath -PathType Leaf)) {
    Write-Diagnostic -Level "FAIL" -Message "Database does not exist: $databaseFullPath"
}
elseif ($python) {
    try {
        $arguments = @($python.Prefix) + @(
            (Join-Path $ProjectRoot "scripts\local_db_ops.py"),
            "inspect", "--db", $databaseFullPath
        )
        $raw = & $python.Executable @arguments 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw ($raw -join [Environment]::NewLine)
        }
        $inspection = ($raw -join "") | ConvertFrom-Json
        if ($inspection.quick_check -eq "ok" -and $inspection.query_only -eq 1) {
            Write-Diagnostic -Level "OK" -Message "SQLite read-only check passed with $($inspection.table_count) tables."
        }
        else {
            Write-Diagnostic -Level "FAIL" -Message "SQLite check failed: $($inspection.quick_check)"
        }
        if (@($inspection.missing_migrations).Count -eq 0) {
            Write-Diagnostic -Level "OK" -Message "Database migrations are complete."
        }
        else {
            $missingMigrationCount = @($inspection.missing_migrations).Count
            Write-Diagnostic -Level "WARN" -Message "$missingMigrationCount migration(s) are pending; start-local will apply them first."
        }
    }
    catch {
        Write-Diagnostic -Level "FAIL" -Message "Database diagnostics failed: $($_.Exception.Message)"
    }
}

if (Test-SmrPort -HostAddress "127.0.0.1" -Port $ApiPort) {
    Write-Diagnostic -Level "WARN" -Message "API port $ApiPort is already in use."
}
else {
    Write-Diagnostic -Level "OK" -Message "API port $ApiPort is available."
}
if (Test-SmrPort -HostAddress "127.0.0.1" -Port $UiPort) {
    Write-Diagnostic -Level "WARN" -Message "UI port $UiPort is already in use."
}
else {
    Write-Diagnostic -Level "OK" -Message "UI port $UiPort is available."
}

if ($env:IFIND_REFRESH_TOKEN) {
    Write-Diagnostic -Level "OK" -Message "iFinD credentials are configured through the environment."
}
else {
    Write-Diagnostic -Level "WARN" -Message "IFIND_REFRESH_TOKEN is not set; offline workflows remain available."
}

Write-Host "Diagnostics complete: $failures failure(s), $warnings warning(s)."
if ($failures -gt 0) {
    exit 1
}
exit 0
