Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$texFile = Join-Path $scriptDir "red_sea_houthi_shipping_paper.tex"
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "paper"

if (!(Test-Path $texFile)) {
    throw "Cannot find LaTeX source: $texFile"
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Push-Location $scriptDir
try {
    for ($i = 1; $i -le 3; $i++) {
        xelatex --interaction=nonstopmode --halt-on-error --output-directory=../paper red_sea_houthi_shipping_paper.tex
    }
}
finally {
    Pop-Location
}

$pdf = Join-Path $outputDir "red_sea_houthi_shipping_paper.pdf"
if (!(Test-Path $pdf)) {
    throw "PDF was not created: $pdf"
}

Write-Host "PDF created: $pdf"
