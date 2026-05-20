# pdf_app TODO

Stack: PyQt6 + PyMuPDF + pypdf + ReportLab + WeasyPrint + LibreOffice. Windows only.

## Phases

- [x] Phase 1: viewer + open PDF, zoom (Ctrl+wheel)
- [x] Phase 2: page ops — merge, split, reorder (drag), delete
- [x] Phase 3: converters — images, office (soffice), html/md (weasyprint), text/csv (reportlab)
- [x] Phase 4: forms fill + image signature stamp
- [x] Phase 5: edit overlays UI — rect-drag in viewer; modes: Pan, Redact, Text, Image, Highlight
- [x] Phase 6: cryptographic signing via pyhanko (.pfx + password UI; invisible PKCS#7)
- [x] Phase 7: annotations — highlight + freehand draw + sticky note
- [x] Phase 8: PyInstaller build script (`build.ps1`); optional icon.ico + optional signtool via env
- [x] Phase 9: installer (`installer.iss`, Inno Setup) — detects LibreOffice + GTK, offers download URLs

## Open issues / decisions

- WeasyPrint on Windows needs GTK runtime. Consider switching to `pdfkit` + wkhtmltopdf (single binary, simpler install) if user friction.
- Office conversion via `soffice` spawns process per file. For batch, reuse single soffice instance with `--accept` socket.
- pypdf `flatten` is best-effort. For reliable form flatten, render via fitz and re-embed.
- "Edit existing text" limit documented in `pdf_edit.py` — true reflow not in scope.

## Resume recipe

```powershell
cd C:\Users\swain\pdf_app
.venv\Scripts\Activate.ps1
git log --oneline   # see last phase
```

Brief Claude: "Resume pdf_app. Read README.md + TODO.md. Continue from next unchecked phase."

## Next concrete tasks

Polish / not-yet-done:
- Drop an actual `icon.ico` at project root — `build.ps1` and `installer.iss` both auto-pick it up.
- Code-sign the exe: set `$env:PDFAPP_SIGN_PFX` + `$env:PDFAPP_SIGN_PWD` before running `build.ps1`.
- Compile installer: `iscc installer.iss` → `dist\installer\pdf_app-setup-0.1.0.exe`.
- Smoke-test `dist\pdf_app.exe` and the installer on a clean VM (verify the missing-deps dialog).
- Optional: visible signature combining `signing.stamp_image` + pyhanko signature field.
