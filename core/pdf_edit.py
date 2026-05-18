"""Edit overlays via PyMuPDF: redact, add text box, replace image region.

Note: true reflow editing of existing text (Acrobat-style) is not feasible
without a layout engine. These ops let you cover and rewrite regions.
"""
from pathlib import Path
import fitz


def redact_rect(src: Path, out: Path, page_index: int, rect: tuple[float, float, float, float]) -> Path:
    doc = fitz.open(src)
    try:
        page = doc.load_page(page_index)
        page.add_redact_annot(fitz.Rect(*rect), fill=(1, 1, 1))
        page.apply_redactions()
        doc.save(out)
    finally:
        doc.close()
    return out


def add_text_box(
    src: Path,
    out: Path,
    page_index: int,
    rect: tuple[float, float, float, float],
    text: str,
    fontsize: float = 11,
    fontname: str = "helv",
    color: tuple[float, float, float] = (0, 0, 0),
) -> Path:
    doc = fitz.open(src)
    try:
        page = doc.load_page(page_index)
        page.insert_textbox(
            fitz.Rect(*rect), text, fontsize=fontsize, fontname=fontname, color=color
        )
        doc.save(out)
    finally:
        doc.close()
    return out


def replace_image(
    src: Path,
    out: Path,
    page_index: int,
    rect: tuple[float, float, float, float],
    image_path: Path,
) -> Path:
    doc = fitz.open(src)
    try:
        page = doc.load_page(page_index)
        # Cover region in white, then place new image
        page.add_redact_annot(fitz.Rect(*rect), fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_image(fitz.Rect(*rect), filename=str(image_path))
        doc.save(out)
    finally:
        doc.close()
    return out
