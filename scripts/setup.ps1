$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
New-Item -ItemType Directory -Force (Join-Path (Split-Path -Parent $projectRoot) 'data/courses') | Out-Null

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw 'Python launcher not found. Install Python 3.10 or newer.'
}

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the virtual environment.' }
}

$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $python -m pip install setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'Failed to install build dependencies.' }
& $python -m pip install --no-build-isolation -e .
if ($LASTEXITCODE -ne 0) { throw 'Failed to install the project.' }
& $python -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Failed to install Chromium.' }
& $python -m nuaa_course doctor
exit $LASTEXITCODE
