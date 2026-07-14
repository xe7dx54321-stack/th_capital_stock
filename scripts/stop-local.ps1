[CmdletBinding()]
param(
    [int]$ApiPort = 3000,
    [int]$UiPort = 5173
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "local-common.ps1")

$ProjectRoot = Get-SmrProjectRoot
$statePath = Get-SmrRuntimeStatePath -ProjectRoot $ProjectRoot -ApiPort $ApiPort -UiPort $UiPort
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    Write-Host "No managed SMR instance was found for API $ApiPort and UI $UiPort."
    exit 0
}

$state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json

function Stop-ManagedProcess {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$ExpectedMarker
    )

    $process = Get-SmrProcess -ProcessId $ProcessId
    if (-not $process) {
        Write-Host "$Name process $ProcessId is already stopped."
        return
    }
    if (-not (Test-SmrOwnedProcess -ProcessId $ProcessId -ProjectRoot $ProjectRoot -ExpectedMarker $ExpectedMarker)) {
        throw "Refusing to stop process $ProcessId because it is not owned by this SMR workspace."
    }

    Stop-Process -Id $ProcessId -Force
    $deadline = [DateTime]::UtcNow.AddSeconds(8)
    while ((Get-SmrProcess -ProcessId $ProcessId) -and [DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 200
    }
    if (Get-SmrProcess -ProcessId $ProcessId) {
        throw "$Name process $ProcessId did not stop within the timeout."
    }
    Write-Host "$Name process $ProcessId stopped."
}

Stop-ManagedProcess -ProcessId ([int]$state.ui_pid) -Name "UI" -ExpectedMarker ([string]$state.ui_marker)
Stop-ManagedProcess -ProcessId ([int]$state.api_pid) -Name "API" -ExpectedMarker ([string]$state.api_marker)
Remove-Item -LiteralPath $statePath -Force
Write-Host "SMR local workbench stopped."
