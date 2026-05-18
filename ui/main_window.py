from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QLabel, QSplitter, QInputDialog,
)
from PyQt6.QtCore import Qt

from pdf_app.ui.pdf_viewer import PdfViewer
from pdf_app.ui.page_panel import PagePanel
from pdf_app.ui.form_panel import FormPanel
from pdf_app.core import pdf_ops
from pdf_app.converters import (
    images_to_pdf,
    office_to_pdf,
    html_md_to_pdf,
    text_csv_to_pdf,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pdf_app")
        self.resize(1280, 800)
        self.current_pdf: Path | None = None

        self._build_menu()
        self._build_ui()

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

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # View/Edit tab
        view_tab = QWidget()
        split = QSplitter(Qt.Orientation.Horizontal, view_tab)
        self.page_panel = PagePanel()
        self.viewer = PdfViewer()
        self.page_panel.page_selected.connect(self.viewer.show_page)
        self.page_panel.pages_changed.connect(self._on_pages_changed)
        split.addWidget(self.page_panel)
        split.addWidget(self.viewer)
        split.setSizes([220, 1060])
        lay = QVBoxLayout(view_tab)
        lay.addWidget(split)
        self.tabs.addTab(view_tab, "View / Edit")

        # Forms tab
        self.form_panel = FormPanel()
        self.tabs.addTab(self.form_panel, "Forms / Sign")

    # File ops
    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF (*.pdf)")
        if not path:
            return
        self.current_pdf = Path(path)
        self.viewer.load(self.current_pdf)
        self.page_panel.load(self.current_pdf)
        self.form_panel.load(self.current_pdf)
        self.setWindowTitle(f"pdf_app — {self.current_pdf.name}")

    def save_as(self):
        if not self.current_pdf:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save As", "", "PDF (*.pdf)")
        if not out:
            return
        try:
            pdf_ops.save_copy(self.current_pdf, Path(out), self.page_panel.order())
            QMessageBox.information(self, "Saved", out)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _on_pages_changed(self):
        # Reload viewer to reflect reorder/delete
        if self.current_pdf:
            self.viewer.load(self.current_pdf)

    # Converters
    def _ask_output(self) -> Path | None:
        out, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF (*.pdf)")
        return Path(out) if out else None

    def convert_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if not paths:
            return
        out = self._ask_output()
        if not out:
            return
        try:
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
            office_to_pdf.convert(Path(path), out)
            QMessageBox.information(self, "Done", str(out))
        except Exception as e:
            QMessageBox.critical(self, "Convert failed", str(e))

    def convert_html_md(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select HTML/Markdown", "", "HTML/MD (*.html *.htm *.md *.markdown)"
        )
        if not path:
            return
        out = self._ask_output()
        if not out:
            return
        try:
            html_md_to_pdf.convert(Path(path), out)
            QMessageBox.information(self, "Done", str(out))
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
            text_csv_to_pdf.convert(Path(path), out)
            QMessageBox.information(self, "Done", str(out))
        except Exception as e:
            QMessageBox.critical(self, "Convert failed", str(e))

    # Page ops
    def merge_pdfs(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to merge", "", "PDF (*.pdf)")
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
        if not self.current_pdf:
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
            files = pdf_ops.split(self.current_pdf, ranges, Path(out_dir))
            QMessageBox.information(self, "Done", "\n".join(str(f) for f in files))
        except Exception as e:
            QMessageBox.critical(self, "Split failed", str(e))
