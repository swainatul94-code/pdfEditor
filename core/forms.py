from pathlib import Path
from pypdf import PdfReader, PdfWriter


def read_fields(path: Path) -> dict[str, str | None]:
    r = PdfReader(str(path))
    fields = r.get_fields() or {}
    out: dict[str, str | None] = {}
    for name, f in fields.items():
        v = f.get("/V")
        out[name] = None if v is None else str(v)
    return out


def fill(src: Path, out: Path, values: dict[str, str]) -> Path:
    r = PdfReader(str(src))
    w = PdfWriter(clone_from=r)
    for page in w.pages:
        w.update_page_form_field_values(page, values)
    with out.open("wb") as f:
        w.write(f)
    return out


def flatten(src: Path, out: Path) -> Path:
    """Flatten form fields (best-effort via pypdf NeedAppearances trick)."""
    r = PdfReader(str(src))
    w = PdfWriter(clone_from=r)
    if "/AcroForm" in w._root_object:
        w._root_object["/AcroForm"].update({})  # noqa: SLF001
    with out.open("wb") as f:
        w.write(f)
    return out
