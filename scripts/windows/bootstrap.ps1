#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ENV_NAME = ".212"
$PYTHON_VERSION = "3.11"

Write-Host "==> Creating conda environment: $ENV_NAME"
$condaBase = (conda info --base).Trim()
$condaHook = Join-Path $condaBase "shell\condabin\conda-hook.ps1"

if (Test-Path $condaHook) {
    & $condaHook
} else {
    Write-Error "Conda PowerShell hook not found at: $condaHook`nRun: conda init powershell"
    exit 1
}

$envExists = conda env list | Select-String -Pattern "^\Q$ENV_NAME\E\b"
if ($envExists) {
    Write-Host "Conda environment $ENV_NAME already exists"
} else {
    conda create -n $ENV_NAME python=$PYTHON_VERSION -y
}

Write-Host "==> Activating conda environment: $ENV_NAME"
conda activate $ENV_NAME

Write-Host "==> Installing uv"
python -m pip install --upgrade pip
pip install uv

Write-Host "==> Installing project dependencies"
$projectDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$requirementsFile = Join-Path $projectDir "requirements.txt"

if (Test-Path $requirementsFile) {
    uv pip install -r $requirementsFile
} else {
    Write-Error "requirements.txt not found at $requirementsFile"
    exit 1
}

Write-Host "==> Bootstrap complete"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. copy .env.example .env"
Write-Host "2. Fill in Trading212 credentials in .env"
Write-Host "3. Run: .\scripts\windows\configure_claude_mcp.ps1"
Write-Host "4. Run: .\scripts\windows\validate_setup.ps1"
