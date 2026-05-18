from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QScrollArea, QLabel, QHBoxLayout, QInputDialog,
)
from pdf_app.core import forms, signing


class FormPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.path: Path | None = None
        self.fields: dict[str, QLineEdit] = {}

        root = QVBoxLayout(self)
        self.info = QLabel("Open a PDF with form fields.")
        root.addWidget(self.info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.form_host = QWidget()
        self.form_layout = QFormLayout(self.form_host)
        scroll.setWidget(self.form_host)
        root.addWidget(scroll)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save filled PDF...")
        save_btn.clicked.connect(self.save_filled)
        sign_btn = QPushButton("Add image signature...")
        sign_btn.clicked.connect(self.add_signature)
        crypto_btn = QPushButton("Digital sign (.pfx)...")
        crypto_btn.clicked.connect(self.digital_sign)
        btns.addWidget(save_btn)
        btns.addWidget(sign_btn)
        btns.addWidget(crypto_btn)
        root.addLayout(btns)

    def load(self, path: Path):
        self.path = path
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.fields.clear()

        data = forms.read_fields(path)
        if not data:
            self.info.setText(f"No AcroForm fields in {path.name}.")
            return
        self.info.setText(f"{len(data)} field(s) in {path.name}.")
        for name, value in data.items():
            edit = QLineEdit(str(value) if value is not None else "")
            self.form_layout.addRow(name, edit)
            self.fields[name] = edit

    def save_filled(self):
        if not self.path or not self.fields:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save filled PDF", "", "PDF (*.pdf)")
        if not out:
            return
        values = {n: e.text() for n, e in self.fields.items()}
        try:
            forms.fill(self.path, Path(out), values)
            QMessageBox.information(self, "Saved", out)
        except Exception as e:
            QMessageBox.critical(self, "Fill failed", str(e))

    def add_signature(self):
        if not self.path:
            return
        img, _ = QFileDialog.getOpenFileName(self, "Signature image", "", "Image (*.png *.jpg)")
        if not img:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save signed PDF", "", "PDF (*.pdf)")
        if not out:
            return
        try:
            signing.stamp_image(
                self.path, Path(out), Path(img), page=-1, x=72, y=72, width=200
            )
            QMessageBox.information(self, "Saved", out)
        except Exception as e:
            QMessageBox.critical(self, "Sign failed", str(e))

    def digital_sign(self):
        if not self.path:
            QMessageBox.warning(self, "No PDF", "Open a PDF first.")
            return
        pfx, _ = QFileDialog.getOpenFileName(
            self, "PKCS#12 cert", "", "PKCS#12 (*.pfx *.p12)"
        )
        if not pfx:
            return
        password, ok = QInputDialog.getText(
            self, "Password", "Cert password:", QLineEdit.EchoMode.Password
        )
        if not ok:
            return
        reason, _ = QInputDialog.getText(self, "Reason", "Reason (optional):")
        location, _ = QInputDialog.getText(self, "Location", "Location (optional):")
        out, _ = QFileDialog.getSaveFileName(
            self, "Save signed PDF", "", "PDF (*.pdf)"
        )
        if not out:
            return
        try:
            signing.sign_pkcs7(
                self.path, Path(out), Path(pfx), password,
                reason=reason or None, location=location or None,
            )
            QMessageBox.information(self, "Signed", out)
        except Exception as e:
            QMessageBox.critical(self, "Digital sign failed", str(e))
