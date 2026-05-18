"""Text / CSV -> PDF via ReportLab."""
import csv
from pathlib import Path
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Preformatted, Table, TableStyle, Spacer,
)


def convert(src: Path, out: Path) -> Path:
    if src.suffix.lower() == ".csv":
        _csv_to_pdf(src, out)
    else:
        _text_to_pdf(src, out)
    return out


def _text_to_pdf(src: Path, out: Path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out), pagesize=LETTER)
    text = src.read_text(encoding="utf-8", errors="replace")
    story = [Preformatted(text, styles["Code"])]
    doc.build(story)


def _csv_to_pdf(src: Path, out: Path):
    with src.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        rows = [["(empty)"]]
    doc = SimpleDocTemplate(str(out), pagesize=landscape(LETTER))
    tbl = Table(rows, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    doc.build([tbl])
