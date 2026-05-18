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

pyinstaller `
    --name pdf_app `
    --windowed `
    --onefile `
    --hidden-import=fitz `
    --hidden-import=weasyprint `
    --hidden-import=reportlab `
    --hidden-import=img2pdf `
    --collect-all PyQt6 `
    --collect-all weasyprint `
    main.py

Write-Host ""
Write-Host "Build complete: dist\pdf_app.exe" -ForegroundColor Green
Write-Host "Note: end-user still needs LibreOffice + GTK runtime installed for Office/HTML conversion." -ForegroundColor Yellow
