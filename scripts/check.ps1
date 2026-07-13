[CmdletBinding()]
param(
    [switch]$Full,
    [switch]$PythonOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Host "==> $Label"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Resolve-Python {
    $localPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if ($env:SMR_PYTHON -and (Test-Path -LiteralPath $env:SMR_PYTHON -PathType Leaf)) {
        return @{ Executable = $env:SMR_PYTHON; Prefix = @() }
    }
    if (Test-Path -LiteralPath $localPython -PathType Leaf) {
        return @{ Executable = $localPython; Prefix = @() }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Executable = $py.Source; Prefix = @("-3") }
        }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Executable = $python.Source; Prefix = @() }
        }
    }
    throw "A working Python 3 was not found. Create .venv or set SMR_PYTHON to python.exe."
}

function Resolve-Node {
    if ($env:SMR_NODE -and (Test-Path -LiteralPath $env:SMR_NODE -PathType Leaf)) {
        return $env:SMR_NODE
    }
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        return $node.Source
    }
    throw "Node.js was not found. Install Node.js 20+ or set SMR_NODE to node.exe."
}

Push-Location $ProjectRoot
try {
    $python = Resolve-Python

    if (-not $PythonOnly) {
        $node = Resolve-Node
        $tsc = Join-Path $ProjectRoot "node_modules\.bin\tsc.cmd"
        if (-not (Test-Path -LiteralPath $tsc -PathType Leaf)) {
            throw "TypeScript is not installed. Run 'npm ci' in $ProjectRoot first."
        }

        Invoke-Checked -Label "TypeScript check" -Executable $tsc -Arguments @("-b", "--noEmit")
        Invoke-Checked -Label "Express API syntax" -Executable $node -Arguments @("--check", "api/server.js")
    }

    $smokeArgs = @($python.Prefix) + @(
        "-m", "unittest", "discover",
        "-s", "tests/smoke",
        "-p", "test*.py",
        "-v"
    )
    Invoke-Checked -Label "Python smoke tests" -Executable $python.Executable -Arguments $smokeArgs

    if ($Full) {
        $inventoryArgs = @($python.Prefix) + @(
            "tools/inventory_repository.py",
            "--check-only"
        )
        Invoke-Checked -Label "Repository inventory audit" -Executable $python.Executable -Arguments $inventoryArgs
    }

    Write-Host "All requested checks passed."
}
finally {
    Pop-Location
}
