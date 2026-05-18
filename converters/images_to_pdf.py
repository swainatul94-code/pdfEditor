from pathlib import Path
import img2pdf


def convert(images: list[Path], out: Path) -> Path:
    with out.open("wb") as f:
        f.write(img2pdf.convert([str(p) for p in images]))
    return out
