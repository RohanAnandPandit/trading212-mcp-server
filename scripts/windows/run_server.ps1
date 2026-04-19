#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ENV_NAME = ".212"
$projectDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$envFile = Join-Path $projectDir ".env"
$condaBase = (conda info --base).Trim()
$condaHook = Join-Path $condaBase "shell\condabin\conda-hook.ps1"

if (Test-Path $condaHook) {
    & $condaHook
} else {
    Write-Error "Conda PowerShell hook not found at: $condaHook`nRun: conda init powershell"
    exit 1
}

conda activate $ENV_NAME

if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '^\s*[^#]' -and $_ -match '=' } | ForEach-Object {
        $parts = $_ -split '=', 2
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

Set-Location $projectDir
python src\server.py
