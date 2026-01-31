# Custom Autocorrect - Test Runner Script
# Usage: Run from project root as Administrator
#   .\scripts\run_tests.ps1
#
# Options:
#   -Verbose    Show detailed test output
#   -Manual     Include manual testing prompts
#   -Quick      Skip property-based tests (faster)

param(
    [switch]$Verbose,
    [switch]$Manual,
    [switch]$Quick
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Custom Autocorrect - Test Runner" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check we're in the right directory
if (-not (Test-Path ".\src\custom_autocorrect\__init__.py")) {
    Write-Host "ERROR: Run this script from the project root directory" -ForegroundColor Red
    Write-Host "  cd C:\path\to\custom-autocorrect" -ForegroundColor Yellow
    Write-Host "  .\scripts\run_tests.ps1" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Green
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "ERROR: Virtual environment not found at .\.venv" -ForegroundColor Red
    Write-Host "Create it with: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Pull latest changes
Write-Host ""
Write-Host "[2/4] Pulling latest changes from GitHub..." -ForegroundColor Green
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: git pull failed - continuing with local code" -ForegroundColor Yellow
}

# Install/update dependencies
Write-Host ""
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Green
pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Run tests
Write-Host ""
Write-Host "[4/4] Running tests..." -ForegroundColor Green
Write-Host ""

$pytestArgs = @("tests/")

if ($Verbose) {
    $pytestArgs += "-v"
} else {
    $pytestArgs += "-v", "--tb=short"
}

if ($Quick) {
    # Skip property-based tests for faster feedback
    $pytestArgs += "--ignore=tests/test_properties.py"
    Write-Host "Skipping property-based tests (Quick mode)" -ForegroundColor Yellow
}

python -m pytest @pytestArgs

$testResult = $LASTEXITCODE

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan

if ($testResult -eq 0) {
    Write-Host "ALL TESTS PASSED!" -ForegroundColor Green
} else {
    Write-Host "SOME TESTS FAILED (exit code: $testResult)" -ForegroundColor Red
    exit $testResult
}

# Manual testing section
if ($Manual) {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "MANUAL TESTING" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""

    # Ensure rules.txt has test rules
    $rulesPath = "$env:USERPROFILE\Documents\CustomAutocorrect\rules.txt"
    $appFolder = "$env:USERPROFILE\Documents\CustomAutocorrect"

    if (-not (Test-Path $appFolder)) {
        New-Item -ItemType Directory -Path $appFolder -Force | Out-Null
    }

    # Check if test rules exist
    $hasTestRules = $false
    if (Test-Path $rulesPath) {
        $content = Get-Content $rulesPath -Raw
        if ($content -match "teh=the") {
            $hasTestRules = $true
        }
    }

    if (-not $hasTestRules) {
        Write-Host "Adding test rules to rules.txt..." -ForegroundColor Yellow
        Add-Content -Path $rulesPath -Value "`n# Test rules for Phase 4`nteh=the`nadn=and`nhte=the"
    }

    Write-Host "Rules file: $rulesPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Manual Test Steps:" -ForegroundColor Yellow
    Write-Host "  1. The app will start - open Notepad" -ForegroundColor White
    Write-Host "  2. Type 'teh ' (with space) -> should become 'the '" -ForegroundColor White
    Write-Host "  3. Type 'Teh ' (with space) -> should become 'The '" -ForegroundColor White
    Write-Host "  4. Type 'TEH ' (with space) -> should become 'THE '" -ForegroundColor White
    Write-Host "  5. Press Ctrl+Z to undo -> should work" -ForegroundColor White
    Write-Host "  6. Press Ctrl+C in this terminal to stop" -ForegroundColor White
    Write-Host ""
    Write-Host "Starting app in 3 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3

    python -m custom_autocorrect
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
