param(
    [Parameter(Mandatory = $true)]
    [string]$Spreadsheet,

    [string]$Credentials = "secrets\google-service-account.json",
    [string]$Range = "",
    [string]$Date = "2026-07-07"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = "C:\Users\Aiffel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$Script = Join-Path $Root "scripts\make_survey_report_auto.py"
$CredentialPath = Join-Path $Root $Credentials
$Pdf = Join-Path $Root "output\reports\student-survey-live-report.pdf"
$Png = Join-Path $Root "output\reports\student-survey-live-report.png"

if (!(Test-Path -LiteralPath $CredentialPath)) {
    throw "Credentials file not found: $CredentialPath"
}

$Args = @(
    $Script,
    "--sheets-id", $Spreadsheet,
    "--credentials", $CredentialPath,
    "--date", $Date,
    "--pdf", $Pdf,
    "--png", $Png
)

if ($Range) {
    $Args += @("--range", $Range)
}

& $Python @Args
