#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$envFile = Join-Path $projectDir ".env"
$clientFile = Join-Path $projectDir "src\utils\client.py"

if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found at $envFile"
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

if (-not $apiKey)      { Write-Error "Missing TRADING212_API_KEY in .env";    exit 1 }
if (-not $apiSecret)   { Write-Error "Missing TRADING212_API_SECRET in .env"; exit 1 }
if (-not $environment) { Write-Error "Missing ENVIRONMENT in .env";           exit 1 }

$authBytes = [System.Text.Encoding]::UTF8.GetBytes("${apiKey}:${apiSecret}")
$auth = [Convert]::ToBase64String($authBytes)

Write-Host "==> Testing Trading212 direct API access"
try {
    $response = Invoke-WebRequest `
        -Uri "https://${environment}.trading212.com/api/v0/equity/account/cash" `
        -Headers @{ Authorization = "Basic $auth" } `
        -UseBasicParsing
    Write-Host "HTTP $($response.StatusCode) $($response.StatusDescription)"
    $response.Content | Select-Object -First 500
} catch {
    Write-Warning "API request failed: $_"
}

Write-Host ""
Write-Host "==> Testing Python client"
python $clientFile

Write-Host ""
Write-Host "==> Testing Claude MCP registration"
claude mcp get trading212
