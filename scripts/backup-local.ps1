[CmdletBinding()]
param(
    [string]$DatabasePath = "01_data/db/smr.db",
    [string]$BackupRoot = "01_data/backups",
    [ValidateRange(1, 3650)][int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "local-common.ps1")

$ProjectRoot = Get-SmrProjectRoot
$databaseFullPath = Resolve-SmrPath -ProjectRoot $ProjectRoot -Path $DatabasePath
$backupRootFullPath = Resolve-SmrPath -ProjectRoot $ProjectRoot -Path $BackupRoot
if (-not (Test-Path -LiteralPath $databaseFullPath -PathType Leaf)) {
    throw "Database does not exist: $databaseFullPath"
}

$python = Resolve-SmrPython -ProjectRoot $ProjectRoot
New-Item -ItemType Directory -Path $backupRootFullPath -Force | Out-Null

$timestamp = [DateTime]::Now.ToString("yyyyMMdd-HHmmss-fff")
$destination = Join-Path $backupRootFullPath "smr-backup-$timestamp.db"
$arguments = @($python.Prefix) + @(
    (Join-Path $ProjectRoot "scripts\local_db_ops.py"),
    "backup",
    "--db", $databaseFullPath,
    "--destination", $destination
)
$raw = & $python.Executable @arguments 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "SQLite online backup failed: $($raw -join [Environment]::NewLine)"
}
$result = ($raw -join "") | ConvertFrom-Json
if ($result.integrity_check -ne "ok") {
    throw "Backup integrity check did not return ok."
}

$rootPrefix = [IO.Path]::GetFullPath($backupRootFullPath).TrimEnd("\") + "\"
$cutoff = [DateTime]::UtcNow.AddDays(-$RetentionDays)
$removed = 0
Get-ChildItem -LiteralPath $backupRootFullPath -Filter "smr-backup-*.db" -File | ForEach-Object {
    $candidate = [IO.Path]::GetFullPath($_.FullName)
    if (-not $candidate.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to prune a backup outside the configured backup root: $candidate"
    }
    if ($_.LastWriteTimeUtc -lt $cutoff) {
        Remove-Item -LiteralPath $candidate -Force
        $removed += 1
    }
}

Write-Host "SQLite backup completed and verified."
Write-Host "Backup: $($result.destination)"
Write-Host "Size: $($result.size_bytes) bytes"
Write-Host "Retention: $RetentionDays day(s); pruned $removed old backup(s)."
