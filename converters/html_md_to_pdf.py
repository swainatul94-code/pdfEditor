"""HTML / Markdown -> PDF via WeasyPrint."""
from pathlib import Path
from urllib.parse import urlparse
import markdown as md
from weasyprint import HTML


def _local_only_fetcher(url: str):
    """url_fetcher that allows only file:// and data: URLs.

    Prevents user-supplied HTML from silently exfiltrating via remote
    images/CSS or pulling in attacker-controlled content. Networked PDFs
    are out of scope for a local desktop converter.
    """
    scheme = urlparse(url).scheme.lower()
    if scheme in ("file", "data", ""):
        from weasyprint import default_url_fetcher
        return default_url_fetcher(url)
    raise ValueError(f"Remote URL fetch blocked: {url}")


def convert(src: Path, out: Path) -> Path:
    suffix = src.suffix.lower()
    if suffix in (".md", ".markdown"):
        html_str = md.markdown(
            src.read_text(encoding="utf-8"),
            extensions=["fenced_code", "tables", "toc"],
        )
        html_str = (
            f"<html><head><meta charset='utf-8'></head><body>{html_str}</body></html>"
        )
        HTML(
            string=html_str,
            base_url=str(src.parent),
            url_fetcher=_local_only_fetcher,
        ).write_pdf(str(out))
    else:
        HTML(
            filename=str(src),
            url_fetcher=_local_only_fetcher,
        ).write_pdf(str(out))
    return out
