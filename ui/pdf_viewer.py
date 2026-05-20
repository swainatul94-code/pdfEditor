from enum import Enum
from pathlib import Path
import fitz
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem,
    QGraphicsPathItem,
)
from PyQt6.QtGui import (
    QPixmap, QImage, QWheelEvent, QPen, QColor, QMouseEvent, QPainterPath,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF


class Mode(str, Enum):
    PAN = "pan"
    REDACT = "redact"
    TEXT = "text"
    IMAGE = "image"
    HIGHLIGHT = "highlight"
    DRAW = "draw"
    NOTE = "note"


RECT_MODES = {Mode.REDACT, Mode.TEXT, Mode.IMAGE, Mode.HIGHLIGHT}


class PdfViewer(QGraphicsView):
    # (page_index, x0, y0, x1, y1) in PDF points
    edit_rect = pyqtSignal(int, float, float, float, float)
    # (page_index, [(x, y), ...]) in PDF points
    edit_path = pyqtSignal(int, list)
    # (page_index, x, y) in PDF points
    edit_point = pyqtSignal(int, float, float)

    def __init__(self):
        super().__init__()
        self.scene_ = QGraphicsScene(self)
        self.setScene(self.scene_)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.doc: fitz.Document | None = None
        self.zoom = 1.5
        self.current_page = 0
        self.mode: Mode = Mode.PAN
        self._drag_start: QPointF | None = None
        self._rubber: QGraphicsRectItem | None = None
        self._ink_points: list[QPointF] = []
        self._ink_path_item: QGraphicsPathItem | None = None

    def set_mode(self, mode: Mode):
        self.mode = mode
        if mode == Mode.PAN:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().unsetCursor()
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def load(self, path: Path):
        if self.doc:
            self.doc.close()
        self.doc = fitz.open(path)
        page = min(self.current_page, self.doc.page_count - 1)
        self.show_page(max(0, page))

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

    # Edit interactions
    def mousePressEvent(self, event: QMouseEvent):
        if not self.doc or event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        if self.mode == Mode.NOTE:
            p = self.mapToScene(event.pos())
            z = self.zoom
            self.edit_point.emit(self.current_page, p.x() / z, p.y() / z)
            event.accept()
            return
        if self.mode == Mode.DRAW:
            p = self.mapToScene(event.pos())
            self._ink_points = [p]
            path = QPainterPath(p)
            self._ink_path_item = QGraphicsPathItem(path)
            pen = QPen(QColor(220, 30, 30))
            pen.setWidth(2)
            self._ink_path_item.setPen(pen)
            self.scene_.addItem(self._ink_path_item)
            event.accept()
            return
        if self.mode in RECT_MODES:
            self._drag_start = self.mapToScene(event.pos())
            self._rubber = QGraphicsRectItem()
            pen = QPen(QColor(220, 30, 30))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            self._rubber.setPen(pen)
            self.scene_.addItem(self._rubber)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._rubber and self._drag_start is not None:
            cur = self.mapToScene(event.pos())
            self._rubber.setRect(QRectF(self._drag_start, cur).normalized())
            event.accept()
            return
        if self._ink_path_item is not None:
            p = self.mapToScene(event.pos())
            self._ink_points.append(p)
            path = QPainterPath(self._ink_points[0])
            for pt in self._ink_points[1:]:
                path.lineTo(pt)
            self._ink_path_item.setPath(path)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._rubber and self._drag_start is not None:
            cur = self.mapToScene(event.pos())
            rect = QRectF(self._drag_start, cur).normalized()
            self.scene_.removeItem(self._rubber)
            self._rubber = None
            self._drag_start = None
            if rect.width() < 3 or rect.height() < 3:
                event.accept()
                return
            z = self.zoom
            self.edit_rect.emit(
                self.current_page,
                rect.x() / z, rect.y() / z,
                (rect.x() + rect.width()) / z,
                (rect.y() + rect.height()) / z,
            )
            event.accept()
            return
        if self._ink_path_item is not None:
            pts = self._ink_points
            self.scene_.removeItem(self._ink_path_item)
            self._ink_path_item = None
            self._ink_points = []
            if len(pts) >= 2:
                z = self.zoom
                self.edit_path.emit(
                    self.current_page,
                    [(p.x() / z, p.y() / z) for p in pts],
                )
            event.accept()
            return
        super().mouseReleaseEvent(event)
