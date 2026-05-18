# pdf_app TODO

Stack: PyQt6 + PyMuPDF + pypdf + ReportLab + WeasyPrint + LibreOffice. Windows only.

## Phases

- [x] Phase 1: viewer + open PDF, zoom (Ctrl+wheel)
- [x] Phase 2: page ops — merge, split, reorder (drag), delete
- [x] Phase 3: converters — images, office (soffice), html/md (weasyprint), text/csv (reportlab)
- [x] Phase 4: forms fill + image signature stamp
- [ ] Phase 5: edit overlays UI — wire `pdf_edit.py` (redact, text box, image replace) to viewer rect-drag tool
- [ ] Phase 6: cryptographic signing via pyhanko (cert + key config UI)
- [ ] Phase 7: annotations — highlight, freehand draw, sticky note
- [ ] Phase 8: package as `.exe` with PyInstaller, bundle icon
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

Phase 5 step 1: add rectangle-drag tool in `ui/pdf_viewer.py`. On mouse release, emit signal with (page_index, rect_in_pdf_coords). MainWindow routes to chosen op (redact / text / replace image). Convert screen rect -> PDF coords by dividing by `self.zoom`.
