# Procure AI Databricks App Deployment Script
# Uses DABs for file sync, then creates/deploys the app

param(
    [string]$Profile = "adb-7181820732839861",
    [string]$AppName = "ds-procure-ai"
)

$ErrorActionPreference = "Stop"

$BundlePath = "/Workspace/Users/harshith.raghunath@etexgroup.com/vendor-agent/files"

Write-Host ""
Write-Host "================================================"
Write-Host "Procure AI Databricks App Deployment"
Write-Host "================================================"
Write-Host "App: $AppName"
Write-Host "Files: $BundlePath"
Write-Host ""

# Step 1: Sync files via DABs
Write-Host "[1/3] Syncing files via DABs..." -ForegroundColor Cyan
& databricks bundle deploy -t dev --profile $Profile
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Bundle failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Files synced" -ForegroundColor Green
Write-Host ""

# Step 2: Create app (if new; continue if already exists)
Write-Host "[2/3] Creating app..." -ForegroundColor Cyan
$ErrorActionPreference = "Continue"
& databricks apps create $AppName --description "Procure AI - AI-powered procurement platform" --no-wait --profile $Profile 2>&1 | Where-Object { $_ -notmatch "already exists" }
$ErrorActionPreference = "Stop"
Write-Host "OK: App ready" -ForegroundColor Green
Write-Host ""

# Step 3: Deploy
Write-Host "[3/3] Deploying..." -ForegroundColor Cyan
& databricks apps deploy $AppName --source-code-path $BundlePath --profile $Profile
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deploy failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Deployed" -ForegroundColor Green
Write-Host ""

# Status
Write-Host "================================================"
Write-Host "Success!" -ForegroundColor Green
Write-Host "================================================"
$app = & databricks apps get $AppName --profile $Profile --output json | ConvertFrom-Json
Write-Host ("URL:    " + $app.url)
Write-Host ("Status: " + $app.app_status.state)
Write-Host ("Compute:" + $app.compute_status.state)
Write-Host ""
