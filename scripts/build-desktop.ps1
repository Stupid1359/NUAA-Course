$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
Set-Location $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $python -m pip install -e '.[desktop]'
if ($LASTEXITCODE -ne 0) { throw '安装桌面应用依赖失败。' }
& $python -m PyInstaller --noconfirm --distpath .cache/desktop-output --workpath .cache/build packaging/desktop.spec
if ($LASTEXITCODE -ne 0) { throw '生成桌面应用失败。' }
$appDir = Join-Path $workspaceRoot 'app'
New-Item -ItemType Directory -Force $appDir | Out-Null
Get-ChildItem -LiteralPath '.cache/desktop-output/课程字幕' | Copy-Item -Destination $appDir -Recurse -Force
Copy-Item -LiteralPath 'docs/desktop.md' -Destination (Join-Path $appDir '使用说明.md')
Write-Host (Join-Path $appDir '课程字幕.exe')
