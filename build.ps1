# Build standalone .exe via PyInstaller.
# Run from pdf_app dir with venv active:
#   .\build.ps1

# Note: do not use $ErrorActionPreference="Stop". PyInstaller writes INFO
# lines to stderr; with Stop the first such line aborts the script. We check
# $LASTEXITCODE explicitly after the pyinstaller call instead.
$ErrorActionPreference = "Continue"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "No .venv found. Create with: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# Use venv python/pyinstaller directly (avoids Activate.ps1 side effects in
# nested PowerShell hosts) and ensure pyinstaller is installed.
$venvPy = ".\.venv\Scripts\python.exe"
$venvPyi = ".\.venv\Scripts\pyinstaller.exe"

& $venvPy -m pip install --disable-pip-version-check pyinstaller | Out-Null

# Clean old build
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }

$pyiArgs = @(
    "--name", "pdf_app",
    "--windowed",
    "--onefile",
    "--hidden-import=fitz",
    "--hidden-import=weasyprint",
    "--hidden-import=reportlab",
    "--hidden-import=img2pdf",
    "--hidden-import=pyhanko",
    "--collect-all", "PyQt6",
    "--collect-all", "weasyprint",
    "--collect-all", "pyhanko",
    "--collect-all", "pyhanko_certvalidator"
)

if (Test-Path "icon.ico") {
    $pyiArgs += @("--icon", "icon.ico")
    Write-Host "Using icon.ico" -ForegroundColor Cyan
} else {
    Write-Host "No icon.ico - default PyInstaller icon will be used." -ForegroundColor Yellow
}

$pyiArgs += "main.py"

& $venvPyi @pyiArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed (exit $LASTEXITCODE)." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Optional code signing: set $env:PDFAPP_SIGN_PFX and $env:PDFAPP_SIGN_PWD
if ($env:PDFAPP_SIGN_PFX -and (Test-Path $env:PDFAPP_SIGN_PFX)) {
    $signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
    if ($signtool) {
        Write-Host "Signing dist\pdf_app.exe..." -ForegroundColor Cyan
        & $signtool sign /f $env:PDFAPP_SIGN_PFX /p $env:PDFAPP_SIGN_PWD `
            /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
            "dist\pdf_app.exe"
    } else {
        Write-Host "signtool.exe not on PATH; skipping signing." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Build complete: dist\pdf_app.exe" -ForegroundColor Green
Write-Host "Note: end-user still needs LibreOffice + GTK runtime installed for Office/HTML conversion." -ForegroundColor Yellow
