import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def _write_safely(w: PdfWriter, src: Path | None, out: Path) -> None:
    """Write writer to out. If out == src, write to temp then atomic replace
    so we don't truncate the file the reader is still holding open."""
    out = Path(out)
    same = src is not None and Path(src).resolve() == out.resolve()
    target = out.with_suffix(out.suffix + ".tmp") if same else out
    with target.open("wb") as f:
        w.write(f)
    if same:
        os.replace(target, out)


def merge(inputs: list[Path], out: Path) -> Path:
    w = PdfWriter()
    src_match: Path | None = None
    out_abs = Path(out).resolve()
    for p in inputs:
        if Path(p).resolve() == out_abs:
            src_match = Path(p)
        r = PdfReader(str(p))
        for page in r.pages:
            w.add_page(page)
    _write_safely(w, src_match, out)
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
    _write_safely(w, src, out)
    return out
