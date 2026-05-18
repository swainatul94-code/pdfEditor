from pathlib import Path
import fitz
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap, QImage, QWheelEvent
from PyQt6.QtCore import Qt


class PdfViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene_ = QGraphicsScene(self)
        self.setScene(self.scene_)
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.doc: fitz.Document | None = None
        self.zoom = 1.5
        self.current_page = 0

    def load(self, path: Path):
        if self.doc:
            self.doc.close()
        self.doc = fitz.open(path)
        self.show_page(0)

    def show_page(self, index: int):
        if not self.doc or index < 0 or index >= self.doc.page_count:
            return
        self.current_page = index
        page = self.doc.load_page(index)
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.scene_.clear()
        self.scene_.addItem(QGraphicsPixmapItem(QPixmap.fromImage(img.copy())))
        self.setSceneRect(0, 0, pix.width, pix.height)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.zoom *= factor
            self.show_page(self.current_page)
        else:
            super().wheelEvent(event)
