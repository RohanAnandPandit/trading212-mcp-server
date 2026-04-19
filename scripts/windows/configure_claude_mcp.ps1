#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ENV_NAME = ".212"
$projectDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$condaBase = (conda info --base).Trim()
$pythonPath = Join-Path $condaBase "envs\$ENV_NAME\python.exe"
$serverPath = Join-Path $projectDir "src\server.py"
$envFile = Join-Path $projectDir ".env"

if (-not (Test-Path $pythonPath)) {
    Write-Error "Python executable not found: $pythonPath`nRun bootstrap.ps1 first."
    exit 1
}

if (-not (Test-Path $serverPath)) {
    Write-Error "Server file not found: $serverPath"
    exit 1
}

if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found at $envFile`nCreate it first: copy .env.example .env"
    exit 1
}

# Load .env variables
Get-Content $envFile | Where-Object { $_ -match '^\s*[^#]' -and $_ -match '=' } | ForEach-Object {
    $parts = $_ -split '=', 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim().Trim('"').Trim("'")
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
}

$apiKey = $env:TRADING212_API_KEY
$apiSecret = $env:TRADING212_API_SECRET
$environment = $env:ENVIRONMENT

if (-not $apiKey)    { Write-Error "Missing TRADING212_API_KEY in .env";    exit 1 }
if (-not $apiSecret) { Write-Error "Missing TRADING212_API_SECRET in .env"; exit 1 }
if (-not $environment) { Write-Error "Missing ENVIRONMENT in .env";         exit 1 }

Write-Host "==> Removing existing local MCP config for trading212 if present"
claude mcp remove trading212 -s local 2>$null
# Ignore exit code — it's fine if it wasn't registered yet

Write-Host "==> Adding Trading212 MCP server to Claude"
claude mcp add trading212 `
    $pythonPath `
    $serverPath `
    -s local `
    -e "TRADING212_API_KEY=$apiKey" `
    -e "TRADING212_API_SECRET=$apiSecret" `
    -e "ENVIRONMENT=$environment"

Write-Host ""
Write-Host "==> MCP registration complete"
claude mcp get trading212
