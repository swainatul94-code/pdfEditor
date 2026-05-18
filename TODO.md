# pdf_app TODO

Stack: PyQt6 + PyMuPDF + pypdf + ReportLab + WeasyPrint + LibreOffice. Windows only.

## Phases

- [x] Phase 1: viewer + open PDF, zoom (Ctrl+wheel)
- [x] Phase 2: page ops — merge, split, reorder (drag), delete
- [x] Phase 3: converters — images, office (soffice), html/md (weasyprint), text/csv (reportlab)
- [x] Phase 4: forms fill + image signature stamp
- [x] Phase 5: edit overlays UI — rect-drag in viewer; modes: Pan, Redact, Text, Image, Highlight
- [x] Phase 6: cryptographic signing via pyhanko (.pfx + password UI; invisible PKCS#7)
- [~] Phase 7: annotations — highlight done; freehand draw + sticky note pending
- [x] Phase 8: PyInstaller build script (`build.ps1`); icon + signed exe pending
- [ ] Phase 9: installer (Inno Setup) — check LibreOffice + GTK deps, prompt install

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

## Next concrete task

Phase 6: cryptographic signing.
- Add `core/signing.py::sign_pkcs7(src, out, pfx_path, password, reason, location)`
- Use `pyhanko.sign.signers.SimpleSigner.load_pkcs12()` + `pyhanko.sign.PdfSigner`
- UI: add "Digital sign..." action in FormPanel — file picker for .pfx, password prompt
- Optional: visible sig combining `stamp_image` + crypto sig (pyhanko signature field)

Phase 7 remainder:
- Freehand draw: capture mouse path in viewer (list of QPointF), emit on release, write via `page.add_ink_annot([points])`
- Sticky note: click position -> `page.add_text_annot(point, text, icon="Note")`

Phase 8 polish:
- Add `icon.ico` to build.ps1 (`--icon icon.ico`)
- Build, smoke-test `dist\pdf_app.exe`
- Sign exe (`signtool`) if cert available

Phase 9:
- Write `installer.iss` (Inno Setup)
- Pre-install check: LibreOffice present? GTK present? Offer download links
