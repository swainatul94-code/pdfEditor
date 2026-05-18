"""Signature support.

stamp_image: visible signature image only (not cryptographic).
For real PKCS#7 signing, add pyhanko flow with a cert/key.
"""
from pathlib import Path
import fitz


def stamp_image(
    src: Path,
    out: Path,
    image: Path,
    page: int = -1,
    x: float = 72,
    y: float = 72,
    width: float = 200,
) -> Path:
    doc = fitz.open(src)
    try:
        idx = page if page >= 0 else doc.page_count - 1
        pg = doc.load_page(idx)
        # Maintain aspect by reading image size
        import PIL.Image
        with PIL.Image.open(image) as im:
            ratio = im.height / im.width
        rect = fitz.Rect(x, y, x + width, y + width * ratio)
        pg.insert_image(rect, filename=str(image))
        doc.save(out)
    finally:
        doc.close()
    return out
