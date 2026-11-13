param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    $python = 'py'
}
Push-Location $projectRoot
& $python -m nuaa_course @Arguments
$result = $LASTEXITCODE
Pop-Location
exit $result
