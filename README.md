# pdf_app

Windows desktop PDF editor + converter. PyQt6 + PyMuPDF.

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

External deps:
- LibreOffice (for Office->PDF): install from libreoffice.org, ensure `soffice.exe` on PATH or set `SOFFICE_PATH` env var.
- GTK runtime (for WeasyPrint HTML/MD->PDF on Windows): https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

## Run

```powershell
python -m pdf_app.main
```

## Features

- Open + view PDF (phase 1, working)
- Page ops: merge, split, reorder, delete (phase 2)
- Convert to PDF: images, Office (docx/xlsx/pptx), HTML/MD, text/CSV (phase 3)
- Forms fill + image signature (phase 4)
- Edit overlays: redact, text box, image replace, highlight (phase 5)
- Annotations: freehand ink + sticky notes (phase 7)
- Crypto signing via .pfx (phase 6)
- PyInstaller exe + Inno Setup installer (phases 8-9)

## Layout

```
pdf_app/
  main.py
  ui/         # PyQt views
  core/       # PDF operations
  converters/ # format -> PDF
```
