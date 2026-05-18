"""HTML / Markdown -> PDF via WeasyPrint."""
from pathlib import Path
import markdown as md
from weasyprint import HTML


def convert(src: Path, out: Path) -> Path:
    suffix = src.suffix.lower()
    if suffix in (".md", ".markdown"):
        html_str = md.markdown(
            src.read_text(encoding="utf-8"),
            extensions=["fenced_code", "tables", "toc"],
        )
        html_str = f"<html><head><meta charset='utf-8'></head><body>{html_str}</body></html>"
        HTML(string=html_str, base_url=str(src.parent)).write_pdf(str(out))
    else:
        HTML(filename=str(src)).write_pdf(str(out))
    return out
