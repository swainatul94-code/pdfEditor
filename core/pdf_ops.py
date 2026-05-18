from pathlib import Path
from pypdf import PdfReader, PdfWriter


def merge(inputs: list[Path], out: Path) -> Path:
    w = PdfWriter()
    for p in inputs:
        r = PdfReader(str(p))
        for page in r.pages:
            w.add_page(page)
    with out.open("wb") as f:
        w.write(f)
    return out


def split(src: Path, ranges_spec: str, out_dir: Path) -> list[Path]:
    """ranges_spec: '1-3,4-6,7' (1-based, inclusive)."""
    r = PdfReader(str(src))
    n = len(r.pages)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    for i, part in enumerate(s.strip() for s in ranges_spec.split(",") if s.strip()):
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            raise ValueError(f"Bad range '{part}' for {n}-page PDF")
        w = PdfWriter()
        for idx in range(start - 1, end):
            w.add_page(r.pages[idx])
        out_path = out_dir / f"{src.stem}_part{i + 1}_{start}-{end}.pdf"
        with out_path.open("wb") as f:
            w.write(f)
        results.append(out_path)
    return results


def save_copy(src: Path, out: Path, page_order: list[int] | None = None) -> Path:
    """Save src to out, optionally reordering/removing pages.
    page_order: list of 0-based source indices in desired order. None = identity."""
    r = PdfReader(str(src))
    w = PdfWriter()
    if page_order is None:
        for page in r.pages:
            w.add_page(page)
    else:
        for idx in page_order:
            w.add_page(r.pages[idx])
    with out.open("wb") as f:
        w.write(f)
    return out
