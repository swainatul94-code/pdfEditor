import os
import shutil
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QTabWidget, QWidget, QVBoxLayout,
    QSplitter, QInputDialog, QToolBar,
)
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt

from pdf_app.ui.pdf_viewer import PdfViewer, Mode
from pdf_app.ui.page_panel import PagePanel
from pdf_app.ui.form_panel import FormPanel
from pdf_app.core import pdf_ops, pdf_edit
# Converters are imported lazily inside each handler. WeasyPrint loads the
# GTK runtime at import time and would crash app startup on machines without
# GTK installed; deferring lets the rest of the app run and surface a
# friendly install hint only when the user actually clicks Convert.


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pdf_app")
        self.resize(1280, 800)
        self.original_pdf: Path | None = None
        self.work_pdf: Path | None = None
        self._tmp_dir = Path(tempfile.gettempdir()) / "pdf_app"
        self._tmp_dir.mkdir(exist_ok=True)

        self._build_menu()
        self._build_toolbar()
        self._build_ui()

    # Working file lifecycle
    def _make_work_copy(self, src: Path) -> Path:
        dest = self._tmp_dir / f"work_{os.getpid()}_{src.name}"
        shutil.copy2(src, dest)
        return dest

    def _cleanup_work(self):
        if self.work_pdf and self.work_pdf.exists():
            try:
                self.work_pdf.unlink()
            except OSError:
                pass
        self.work_pdf = None

    def closeEvent(self, event):
        self._cleanup_work()
        super().closeEvent(event)

    # UI build
    def _build_menu(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("&File")
        file_menu.addAction("Open PDF...", self.open_pdf)
        file_menu.addAction("Save As...", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        conv_menu = mb.addMenu("&Convert to PDF")
        conv_menu.addAction("Images...", self.convert_images)
        conv_menu.addAction("Office (docx/xlsx/pptx)...", self.convert_office)
        conv_menu.addAction("HTML / Markdown...", self.convert_html_md)
        conv_menu.addAction("Text / CSV...", self.convert_text_csv)

        pages_menu = mb.addMenu("&Pages")
        pages_menu.addAction("Merge PDFs...", self.merge_pdfs)
        pages_menu.addAction("Split current PDF...", self.split_pdf)

    def _build_toolbar(self):
        tb = QToolBar("Edit", self)
        tb.setMovable(False)
        self.addToolBar(tb)
        group = QActionGroup(self)
        group.setExclusive(True)
        self.mode_actions: dict[Mode, QAction] = {}
        for label, mode in [
            ("Pan", Mode.PAN),
            ("Redact", Mode.REDACT),
            ("Text", Mode.TEXT),
            ("Replace text", Mode.REPLACE_TEXT),
            ("Image", Mode.IMAGE),
            ("Highlight", Mode.HIGHLIGHT),
            ("Draw", Mode.DRAW),
            ("Note", Mode.NOTE),
        ]:
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda _checked, m=mode: self._set_mode(m))
            group.addAction(act)
            tb.addAction(act)
            self.mode_actions[mode] = act
        self.mode_actions[Mode.PAN].setChecked(True)

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        view_tab = QWidget()
        split = QSplitter(Qt.Orientation.Horizontal, view_tab)
        self.page_panel = PagePanel()
        self.viewer = PdfViewer()
        self.page_panel.page_selected.connect(self.viewer.show_page)
        self.page_panel.pages_changed.connect(self._on_pages_changed)
        self.viewer.edit_rect.connect(self._on_edit_rect)
        self.viewer.edit_path.connect(self._on_edit_path)
        self.viewer.edit_point.connect(self._on_edit_point)
        split.addWidget(self.page_panel)
        split.addWidget(self.viewer)
        split.setSizes([220, 1060])
        lay = QVBoxLayout(view_tab)
        lay.addWidget(split)
        self.tabs.addTab(view_tab, "View / Edit")

        self.form_panel = FormPanel()
        self.tabs.addTab(self.form_panel, "Forms / Sign")

    def _set_mode(self, mode: Mode):
        self.viewer.set_mode(mode)

    # File ops
    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF (*.pdf)")
        if not path:
            return
        self._cleanup_work()
        self.original_pdf = Path(path)
        self.work_pdf = self._make_work_copy(self.original_pdf)
        self.viewer.load(self.work_pdf)
        self.page_panel.load(self.work_pdf)
        self.form_panel.load(self.work_pdf)
        self.setWindowTitle(f"pdf_app — {self.original_pdf.name}")

    def save_as(self):
        if not self.work_pdf:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save As", "", "PDF (*.pdf)")
        if not out:
            return
        try:
            shutil.copy2(self.work_pdf, out)
            QMessageBox.information(self, "Saved", out)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _on_pages_changed(self):
        if not self.work_pdf:
            return
        # Apply current panel order/deletions to work_pdf so the viewer (and
        # later edit ops, which address pages by their viewer index) see the
        # same page set the panel shows.
        order = self.page_panel.order()
        try:
            if order:
                pdf_ops.save_copy(self.work_pdf, self.work_pdf, order)
            self.viewer.load(self.work_pdf)
            # Reload panel so its UserRole indices are 0..N-1 again, matching
            # the just-written file.
            self.page_panel.blockSignals(True)
            self.page_panel.load(self.work_pdf)
            self.page_panel.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Page change failed", str(e))

    # Edit ops (rect-drag)
    def _on_edit_rect(self, page: int, x0: float, y0: float, x1: float, y1: float):
        if not self.work_pdf:
            return
        rect = (x0, y0, x1, y1)
        mode = self.viewer.mode
        try:
            if mode == Mode.REDACT:
                pdf_edit.redact_rect(self.work_pdf, self.work_pdf, page, rect)
            elif mode == Mode.TEXT:
                text, ok = QInputDialog.getMultiLineText(self, "Insert text", "Text:")
                if not ok or not text:
                    return
                size, ok2 = QInputDialog.getDouble(
                    self, "Font size", "Size (pt):", 11.0, 4.0, 144.0, 1
                )
                if not ok2:
                    return
                pdf_edit.add_text_box(
                    self.work_pdf, self.work_pdf, page, rect, text, fontsize=size
                )
            elif mode == Mode.REPLACE_TEXT:
                text, ok = QInputDialog.getMultiLineText(
                    self, "Replace text", "Replacement:"
                )
                if not ok or not text:
                    return
                size, ok2 = QInputDialog.getDouble(
                    self, "Font size", "Size (pt):", 11.0, 4.0, 144.0, 1
                )
                if not ok2:
                    return
                pdf_edit.replace_text_box(
                    self.work_pdf, self.work_pdf, page, rect, text, fontsize=size
                )
            elif mode == Mode.IMAGE:
                img, _ = QFileDialog.getOpenFileName(
                    self, "Image", "", "Image (*.png *.jpg *.jpeg *.bmp)"
                )
                if not img:
                    return
                pdf_edit.replace_image(
                    self.work_pdf, self.work_pdf, page, rect, Path(img)
                )
            elif mode == Mode.HIGHLIGHT:
                pdf_edit.highlight_rect(self.work_pdf, self.work_pdf, page, rect)
            else:
                return
            # Reload viewer only; reloading page_panel would wipe the user's
            # current reorder/delete state.
            self.viewer.load(self.work_pdf)
        except Exception as e:
            QMessageBox.critical(self, "Edit failed", str(e))

    def _on_edit_path(self, page: int, points: list):
        if not self.work_pdf or self.viewer.mode != Mode.DRAW:
            return
        try:
            pdf_edit.add_ink_annot(self.work_pdf, self.work_pdf, page, points)
            self.viewer.load(self.work_pdf)
        except Exception as e:
            QMessageBox.critical(self, "Draw failed", str(e))

    def _on_edit_point(self, page: int, x: float, y: float):
        if not self.work_pdf or self.viewer.mode != Mode.NOTE:
            return
        text, ok = QInputDialog.getMultiLineText(self, "Sticky note", "Note text:")
        if not ok or not text:
            return
        try:
            pdf_edit.add_note_annot(self.work_pdf, self.work_pdf, page, x, y, text)
            self.viewer.load(self.work_pdf)
        except Exception as e:
            QMessageBox.critical(self, "Note failed", str(e))

    # Converters
    def _ask_output(self) -> Path | None:
        out, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF (*.pdf)")
        return Path(out) if out else None

    def convert_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not paths:
            return
        out = self._ask_output()
        if not out:
            return
        try:
            from pdf_app.converters import images_to_pdf
            images_to_pdf.convert([Path(p) for p in paths], out)
            QMessageBox.information(self, "Done", str(out))
        except Exception as e:
            QMessageBox.critical(self, "Convert failed", str(e))

    def convert_office(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Office file", "",
            "Office (*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.odt *.ods *.odp)",
        )
        if not path:
            return
        out = self._ask_output()
        if not out:
            return
        try:
            from pdf_app.converters import office_to_pdf
            office_to_pdf.convert(Path(path), out)
            QMessageBox.information(self, "Done", str(out))
        except FileNotFoundError as e:
            QMessageBox.critical(
                self, "LibreOffice not found",
                "Office -> PDF conversion needs LibreOffice.\n\n"
                "Install: https://www.libreoffice.org/download/download/\n\n"
                "Or set the SOFFICE_PATH environment variable to point at\n"
                "your soffice.exe.\n\n"
                f"Detail: {e}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Convert failed", str(e))

    def convert_html_md(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select HTML/Markdown", "",
            "HTML/MD (*.html *.htm *.md *.markdown)",
        )
        if not path:
            return
        out = self._ask_output()
        if not out:
            return
        try:
            from pdf_app.converters import html_md_to_pdf
            html_md_to_pdf.convert(Path(path), out)
            QMessageBox.information(self, "Done", str(out))
        except OSError as e:
            # WeasyPrint raises OSError on Windows when GTK / Pango cannot
            # be located (cffi load failure).
            QMessageBox.critical(
                self, "GTK runtime missing",
                "HTML/Markdown -> PDF conversion needs the GTK 3 runtime.\n\n"
                "Install: https://github.com/tschoonj/GTK-for-Windows-Runtime"
                "-Environment-Installer/releases\n\n"
                "Then restart this app.\n\n"
                f"Detail: {e}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Convert failed", str(e))

    def convert_text_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select text/CSV", "", "Text (*.txt *.csv *.log)"
        )
        if not path:
            return
        out = self._ask_output()
        if not out:
            return
        try:
            from pdf_app.converters import text_csv_to_pdf
            text_csv_to_pdf.convert(Path(path), out)
            QMessageBox.information(self, "Done", str(out))
        except Exception as e:
            QMessageBox.critical(self, "Convert failed", str(e))

    # Page ops
    def merge_pdfs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDFs to merge", "", "PDF (*.pdf)"
        )
        if not paths:
            return
        out = self._ask_output()
        if not out:
            return
        try:
            pdf_ops.merge([Path(p) for p in paths], out)
            QMessageBox.information(self, "Done", str(out))
        except Exception as e:
            QMessageBox.critical(self, "Merge failed", str(e))

    def split_pdf(self):
        if not self.work_pdf:
            QMessageBox.warning(self, "No PDF", "Open a PDF first.")
            return
        ranges, ok = QInputDialog.getText(
            self, "Split", "Page ranges (e.g. 1-3,4-6,7):"
        )
        if not ok or not ranges.strip():
            return
        out_dir = QFileDialog.getExistingDirectory(self, "Output folder")
        if not out_dir:
            return
        try:
            files = pdf_ops.split(self.work_pdf, ranges, Path(out_dir))
            QMessageBox.information(self, "Done", "\n".join(str(f) for f in files))
        except Exception as e:
            QMessageBox.critical(self, "Split failed", str(e))
