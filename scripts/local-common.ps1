Set-StrictMode -Version Latest

function Get-SmrProjectRoot {
    return [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
}

function Resolve-SmrPath {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectRoot,
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Path))
}

function Resolve-SmrPython {
    param([Parameter(Mandatory = $true)][string]$ProjectRoot)

    $localPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if ($env:SMR_PYTHON -and (Test-Path -LiteralPath $env:SMR_PYTHON -PathType Leaf)) {
        return [pscustomobject]@{ Executable = $env:SMR_PYTHON; Prefix = @() }
    }
    if (Test-Path -LiteralPath $localPython -PathType Leaf) {
        return [pscustomobject]@{ Executable = $localPython; Prefix = @() }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{ Executable = $py.Source; Prefix = @("-3") }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{ Executable = $python.Source; Prefix = @() }
        }
    }
    throw "Python 3 was not found. Create .venv or set SMR_PYTHON."
}

function Resolve-SmrNode {
    if ($env:SMR_NODE -and (Test-Path -LiteralPath $env:SMR_NODE -PathType Leaf)) {
        return $env:SMR_NODE
    }
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        return $node.Source
    }
    throw "Node.js was not found. Install Node.js 20+ or set SMR_NODE."
}

function Test-SmrPort {
    param(
        [Parameter(Mandatory = $true)][string]$HostAddress,
        [Parameter(Mandatory = $true)][int]$Port,
        [int]$TimeoutMilliseconds = 300
    )

    $client = [Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.BeginConnect($HostAddress, $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) {
            return $false
        }
        $client.EndConnect($pending)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Get-SmrRuntimeStatePath {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectRoot,
        [Parameter(Mandatory = $true)][int]$ApiPort,
        [Parameter(Mandatory = $true)][int]$UiPort
    )

    $stateDirectory = Join-Path $ProjectRoot ".tmp\local-runtime"
    return Join-Path $stateDirectory "runtime-$ApiPort-$UiPort.json"
}

function Get-SmrProcess {
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    return Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
}

function Test-SmrOwnedProcess {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][string]$ProjectRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedMarker,
        [string]$ExpectedExecutable,
        [string]$ExpectedStartTimeUtc
    )

    $process = Get-SmrProcess -ProcessId $ProcessId
    if (-not $process) {
        return $false
    }

    $cimProcess = Get-CimInstance Win32_Process `
        -Filter "ProcessId = $ProcessId" `
        -ErrorAction SilentlyContinue
    if ($cimProcess) {
        $commandLine = [string]$cimProcess.CommandLine
        if ($commandLine.Contains($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -and
            $commandLine.Contains($ExpectedMarker, [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    if (-not $ExpectedExecutable -or -not $ExpectedStartTimeUtc) {
        return $false
    }
    try {
        $actualExecutable = [IO.Path]::GetFullPath($process.Path)
        $expectedExecutableFullPath = [IO.Path]::GetFullPath($ExpectedExecutable)
        $actualStartedAt = $process.StartTime.ToUniversalTime()
        $expectedStartedAt = [DateTime]::Parse(
            $ExpectedStartTimeUtc,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind
        ).ToUniversalTime()
        $sameExecutable = $actualExecutable.Equals(
            $expectedExecutableFullPath,
            [StringComparison]::OrdinalIgnoreCase
        )
        $sameStartTime = [Math]::Abs(
            ($actualStartedAt - $expectedStartedAt).TotalSeconds
        ) -lt 1
        return $sameExecutable -and $sameStartTime
    }
    catch {
        return $false
    }
}

function Wait-SmrHttp {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 25
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }
    return $false
}
