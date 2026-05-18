"""Office -> PDF via LibreOffice headless (soffice).

Requires LibreOffice installed. Path resolved from SOFFICE_PATH env var,
common install locations, or PATH.
"""
import os
import shutil
import subprocess
from pathlib import Path


_DEFAULT_LOCATIONS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def _find_soffice() -> str:
    env = os.environ.get("SOFFICE_PATH")
    if env and Path(env).exists():
        return env
    for p in _DEFAULT_LOCATIONS:
        if Path(p).exists():
            return p
    found = shutil.which("soffice") or shutil.which("soffice.exe")
    if found:
        return found
    raise FileNotFoundError(
        "soffice not found. Install LibreOffice or set SOFFICE_PATH env var."
    )


def convert(src: Path, out: Path) -> Path:
    soffice = _find_soffice()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice, "--headless", "--norestore", "--nologo",
        "--convert-to", "pdf", "--outdir", str(out.parent), str(src),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"soffice failed: {result.stderr or result.stdout}")
    generated = out.parent / (src.stem + ".pdf")
    if generated != out:
        if out.exists():
            out.unlink()
        generated.rename(out)
    return out
