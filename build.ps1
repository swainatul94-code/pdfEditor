# Build standalone .exe via PyInstaller.
# Run from pdf_app dir with venv active:
#   .\build.ps1

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "No .venv found. Create with: python -m venv .venv" -ForegroundColor Red
    exit 1
}

& .\.venv\Scripts\Activate.ps1

pip install pyinstaller

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
    Write-Host "No icon.ico — default PyInstaller icon will be used." -ForegroundColor Yellow
}

$pyiArgs += "main.py"

pyinstaller @pyiArgs

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
