"""Edit overlays via PyMuPDF: redact, add text box, replace image, highlight.

Note: true reflow editing of existing text (Acrobat-style) is not feasible
without a layout engine. These ops cover regions and overlay new content.

All ops support src == out (writes to temp + atomic replace).
"""
import os
from pathlib import Path
import fitz


def _save(doc: fitz.Document, src: Path, out: Path) -> None:
    src, out = Path(src), Path(out)
    if src.resolve() == out.resolve():
        tmp = out.with_suffix(out.suffix + ".tmp")
        doc.save(str(tmp), garbage=4, deflate=True)
        doc.close()
        os.replace(tmp, out)
    else:
        doc.save(str(out), garbage=4, deflate=True)
        doc.close()


def redact_rect(
    src: Path,
    out: Path,
    page_index: int,
    rect: tuple[float, float, float, float],
) -> Path:
    doc = fitz.open(str(src))
    try:
        page = doc.load_page(page_index)
        page.add_redact_annot(fitz.Rect(*rect), fill=(1, 1, 1))
        page.apply_redactions()
        _save(doc, src, out)
    except Exception:
        doc.close()
        raise
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
    doc = fitz.open(str(src))
    try:
        page = doc.load_page(page_index)
        page.insert_textbox(
            fitz.Rect(*rect), text, fontsize=fontsize, fontname=fontname, color=color
        )
        _save(doc, src, out)
    except Exception:
        doc.close()
        raise
    return out


def replace_image(
    src: Path,
    out: Path,
    page_index: int,
    rect: tuple[float, float, float, float],
    image_path: Path,
) -> Path:
    doc = fitz.open(str(src))
    try:
        page = doc.load_page(page_index)
        page.add_redact_annot(fitz.Rect(*rect), fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_image(fitz.Rect(*rect), filename=str(image_path))
        _save(doc, src, out)
    except Exception:
        doc.close()
        raise
    return out


def highlight_rect(
    src: Path,
    out: Path,
    page_index: int,
    rect: tuple[float, float, float, float],
    color: tuple[float, float, float] = (1, 1, 0),
    opacity: float = 0.35,
) -> Path:
    doc = fitz.open(str(src))
    try:
        page = doc.load_page(page_index)
        annot = page.add_rect_annot(fitz.Rect(*rect))
        annot.set_colors(stroke=color, fill=color)
        annot.set_opacity(opacity)
        annot.set_border(width=0)
        annot.update()
        _save(doc, src, out)
    except Exception:
        doc.close()
        raise
    return out
