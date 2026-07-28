[CmdletBinding()]
param(
    [ValidateSet("127.0.0.1")][string]$HostAddress = "127.0.0.1",
    [int]$ApiPort = 3000,
    [int]$UiPort = 5173,
    [string]$DatabasePath = "01_data/db/smr.db",
    [string]$SourceDatabasePath = "../th_capital_stock/01_data/db/smr.db",
    [switch]$SkipDoctor,
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "local-common.ps1")

$ProjectRoot = Get-SmrProjectRoot
$databaseFullPath = Resolve-SmrPath -ProjectRoot $ProjectRoot -Path $DatabasePath
$sourceDatabaseFullPath = Resolve-SmrPath -ProjectRoot $ProjectRoot -Path $SourceDatabasePath
$statePath = Get-SmrRuntimeStatePath -ProjectRoot $ProjectRoot -ApiPort $ApiPort -UiPort $UiPort
$stateDirectory = Split-Path -Parent $statePath
$logDirectory = Join-Path $ProjectRoot "10_logs\dev"
$apiEntry = Join-Path $ProjectRoot "api\server.js"
$viteEntry = Join-Path $ProjectRoot "node_modules\vite\bin\vite.js"

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    try {
        $existingState = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
        $apiOwned = Test-SmrOwnedProcess `
            -ProcessId ([int]$existingState.api_pid) `
            -ProjectRoot $ProjectRoot `
            -ExpectedMarker "api\server.js" `
            -ExpectedExecutable ([string]$existingState.node_path) `
            -ExpectedStartTimeUtc ([string]$existingState.api_started_at)
        $uiOwned = Test-SmrOwnedProcess `
            -ProcessId ([int]$existingState.ui_pid) `
            -ProjectRoot $ProjectRoot `
            -ExpectedMarker "vite\bin\vite.js" `
            -ExpectedExecutable ([string]$existingState.node_path) `
            -ExpectedStartTimeUtc ([string]$existingState.ui_started_at)
        if ($apiOwned -and $uiOwned) {
            Write-Host "SMR is already running."
            Write-Host "UI:  http://$HostAddress`:$UiPort/workbench"
            Write-Host "API: http://$HostAddress`:$ApiPort/api/health"
            exit 0
        }
    }
    catch {
        Write-Warning "Ignoring an unreadable local runtime state file."
    }
    Remove-Item -LiteralPath $statePath -Force
}

if (-not $SkipDoctor) {
    & (Join-Path $PSScriptRoot "doctor.ps1") -DatabasePath $databaseFullPath -ApiPort $ApiPort -UiPort $UiPort
    if ($LASTEXITCODE -ne 0) {
        throw "Local diagnostics failed. Resolve the FAIL items before starting."
    }
}

if (Test-SmrPort -HostAddress $HostAddress -Port $ApiPort) {
    throw "API port $ApiPort is already in use."
}
if (Test-SmrPort -HostAddress $HostAddress -Port $UiPort) {
    throw "UI port $UiPort is already in use."
}
if (-not (Test-Path -LiteralPath $databaseFullPath -PathType Leaf)) {
    throw "Database does not exist: $databaseFullPath"
}
if (-not (Test-Path -LiteralPath $sourceDatabaseFullPath -PathType Leaf)) {
    throw "Research source database does not exist: $sourceDatabaseFullPath"
}
if (-not (Test-Path -LiteralPath $viteEntry -PathType Leaf)) {
    throw "Vite is not installed. Run npm ci first."
}

$python = Resolve-SmrPython -ProjectRoot $ProjectRoot
$node = Resolve-SmrNode
$migrationArguments = @($python.Prefix) + @(
    "-m", "smr_app", "migrate", "--db-path", $databaseFullPath
)
& $python.Executable @migrationArguments
if ($LASTEXITCODE -ne 0) {
    throw "Database migration check failed with exit code $LASTEXITCODE."
}

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

$apiStdout = Join-Path $logDirectory "local-$ApiPort-api.stdout.log"
$apiStderr = Join-Path $logDirectory "local-$ApiPort-api.stderr.log"
$uiStdout = Join-Path $logDirectory "local-$UiPort-ui.stdout.log"
$uiStderr = Join-Path $logDirectory "local-$UiPort-ui.stderr.log"

$previousHost = $env:HOST
$previousPort = $env:PORT
$previousDatabase = $env:SMR_DB_PATH
$previousSourceDatabase = $env:SMR_SOURCE_DB_PATH
$previousPython = $env:SMR_PYTHON
$previousApiOrigin = $env:SMR_API_ORIGIN
$apiProcess = $null
$uiProcess = $null

# Some launchers provide both Path and PATH. Windows treats those names as the
# same variable, but Windows PowerShell 5.1 Start-Process builds a case-insensitive
# dictionary and fails when both entries are present. Recreate one canonical
# process-scoped entry before launching child processes.
$processPath = [Environment]::GetEnvironmentVariable(
    "Path",
    [EnvironmentVariableTarget]::Process
)
[Environment]::SetEnvironmentVariable(
    "PATH",
    $null,
    [EnvironmentVariableTarget]::Process
)
[Environment]::SetEnvironmentVariable(
    "Path",
    $processPath,
    [EnvironmentVariableTarget]::Process
)

try {
    $env:HOST = $HostAddress
    $env:PORT = [string]$ApiPort
    $env:SMR_DB_PATH = $databaseFullPath
    $env:SMR_SOURCE_DB_PATH = $sourceDatabaseFullPath
    $env:SMR_PYTHON = $python.Executable
    $env:SMR_API_ORIGIN = "http://$HostAddress`:$ApiPort"

    $apiProcess = Start-Process -FilePath $node `
        -ArgumentList @("`"$apiEntry`"") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $apiStdout `
        -RedirectStandardError $apiStderr `
        -WindowStyle Hidden `
        -PassThru

    $uiProcess = Start-Process -FilePath $node `
        -ArgumentList @("`"$viteEntry`"", "--host", $HostAddress, "--port", [string]$UiPort, "--strictPort") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $uiStdout `
        -RedirectStandardError $uiStderr `
        -WindowStyle Hidden `
        -PassThru
}
catch {
    if ($uiProcess -and -not $uiProcess.HasExited) {
        Stop-Process -Id $uiProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    }
    throw
}
finally {
    $env:HOST = $previousHost
    $env:PORT = $previousPort
    $env:SMR_DB_PATH = $previousDatabase
    $env:SMR_SOURCE_DB_PATH = $previousSourceDatabase
    $env:SMR_PYTHON = $previousPython
    $env:SMR_API_ORIGIN = $previousApiOrigin
}

$state = [ordered]@{
    project_root = $ProjectRoot
    host = $HostAddress
    api_port = $ApiPort
    ui_port = $UiPort
    database_path = $databaseFullPath
    source_database_path = $sourceDatabaseFullPath
    node_path = $node
    api_pid = $apiProcess.Id
    ui_pid = $uiProcess.Id
    api_started_at = $apiProcess.StartTime.ToUniversalTime().ToString("o")
    ui_started_at = $uiProcess.StartTime.ToUniversalTime().ToString("o")
    api_marker = "api\server.js"
    ui_marker = "vite\bin\vite.js"
    started_at = [DateTime]::UtcNow.ToString("o")
}
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8

$apiReady = Wait-SmrHttp -Url "http://$HostAddress`:$ApiPort/api/health"
$uiReady = Wait-SmrHttp -Url "http://$HostAddress`:$UiPort/"
if (-not ($apiReady -and $uiReady)) {
    & (Join-Path $PSScriptRoot "stop-local.ps1") -ApiPort $ApiPort -UiPort $UiPort
    throw "Local services did not become ready. Review logs under $logDirectory."
}

Write-Host "SMR local workbench started."
Write-Host "UI:  http://$HostAddress`:$UiPort/workbench"
Write-Host "API: http://$HostAddress`:$ApiPort/api/health"
Write-Host "State: $statePath"
if ($OpenBrowser) {
    Start-Process "http://$HostAddress`:$UiPort/workbench"
}
