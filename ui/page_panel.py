from pathlib import Path
import fitz
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage, QAction


class PagePanel(QListWidget):
    page_selected = pyqtSignal(int)
    pages_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(140, 180))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Snap)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx)
        self.itemClicked.connect(self._on_click)
        self.model().rowsMoved.connect(lambda *a: self.pages_changed.emit())
        self.path: Path | None = None

    def load(self, path: Path):
        self.path = path
        self.clear()
        doc = fitz.open(path)
        try:
            for i in range(doc.page_count):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                icon = QIcon(QPixmap.fromImage(img.copy()))
                item = QListWidgetItem(icon, f"{i + 1}")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.addItem(item)
        finally:
            doc.close()

    def _on_click(self, item: QListWidgetItem):
        idx = self.row(item)
        self.page_selected.emit(idx)

    def _ctx(self, pos):
        item = self.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        act_del = QAction("Delete page(s)", self)
        act_del.triggered.connect(self._delete_selected)
        menu.addAction(act_del)
        menu.exec(self.mapToGlobal(pos))

    def _delete_selected(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        self.pages_changed.emit()

    def order(self) -> list[int]:
        """Original page indices in current display order."""
        return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]
