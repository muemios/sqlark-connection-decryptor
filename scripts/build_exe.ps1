<#
.SYNOPSIS
    Build a standalone Windows executable with PyInstaller.

.DESCRIPTION
    Thin wrapper around scripts/build_binary.py, which derives the artifact
    name from version + platform + architecture, e.g.
    sqlark-connection-decryptor-v0.1.1-windows-x64.exe

.PARAMETER Python
    Python interpreter to use. Defaults to "python".

.PARAMETER Variant
    "gui" (windowed, default) or "cli" (console).

.PARAMETER Version
    Override the version from sqlark_decrypt/__version__.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
    powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1 -Variant cli
#>
param(
    [string]$Python = "python",
    [ValidateSet("gui", "cli")]
    [string]$Variant = "gui",
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    & $Python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller not found, installing..."
        & $Python -m pip install "pyinstaller>=6"
        if ($LASTEXITCODE -ne 0) { throw "Failed to install PyInstaller" }
    }

    $arguments = @("scripts\build_binary.py", "--variant", $Variant)
    if ($Version) { $arguments += @("--version", $Version) }

    & $Python @arguments
    if ($LASTEXITCODE -ne 0) { throw "Build failed (exit $LASTEXITCODE)" }
}
finally {
    Pop-Location
}
