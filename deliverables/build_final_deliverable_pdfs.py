#!/usr/bin/env python3
"""Build PDF copies of the final UniNest text deliverables."""

from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted

HERE = Path(__file__).resolve().parent
OUT = HERE / "Final_Deliverables"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "UniNest_SRS.pdf": "UniNest_SRS.md",
    "UniNest_SDS.pdf": "UniNest_SDS.md",
    "UniNest_Test_Plan.pdf": "UniNest_Test_Plan.md",
    "UniNest_Implementation_Plan.pdf": "UniNest_Implementation_Plan.md",
    "UniNest_Final_Report.pdf": "UniNest_Final_Report.md",
    "UniNest_User_Manual.pdf": "User_Manual.md",
}

FONT_DIR = next((p for p in (
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/data/data/com.termux/files/usr/share/fonts/TTF"),
) if (p / "DejaVuSans.ttf").is_file()), Path("/usr/share/fonts/truetype/dejavu"))

if (FONT_DIR / "DejaVuSans.ttf").is_file():
    pdfmetrics.registerFont(TTFont("DV", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DV-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    NORMAL, BOLD = "DV", "DV-Bold"
else:
    NORMAL, BOLD = "Helvetica", "Helvetica-Bold"


def esc(text):
    import html
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', text)
    return text


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(NORMAL, 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(18 * mm, 12 * mm, "UniNest — University Hostel Management System")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def table_from(lines):
    rows = []
    for line in lines:
        if re.match(r"^\|\s*:?-", line):
            continue
        cells = [esc(c.strip()) for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return None
    width = (A4[0] - 36 * mm) / len(rows[0])
    table = Table(rows, colWidths=[width] * len(rows[0]), repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), BOLD),
        ("FONTNAME", (0, 1), (-1, -1), NORMAL),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("LEADING", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9BA8B7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FB")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def build(source_name, output_name):
    source = HERE / source_name
    output = OUT / output_name
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="UniTitle", parent=styles["Title"], fontName=BOLD, fontSize=20, textColor=colors.HexColor("#1F3864"), leading=24, spaceAfter=14))
    styles.add(ParagraphStyle(name="UniH1", parent=styles["Heading1"], fontName=BOLD, fontSize=16, textColor=colors.HexColor("#1F3864"), leading=20, spaceBefore=12, spaceAfter=7))
    styles.add(ParagraphStyle(name="UniH2", parent=styles["Heading2"], fontName=BOLD, fontSize=12, textColor=colors.HexColor("#2E75B6"), leading=15, spaceBefore=9, spaceAfter=5))
    styles.add(ParagraphStyle(name="UniBody", parent=styles["BodyText"], fontName=NORMAL, fontSize=9.5, leading=13.5, spaceAfter=5))
    styles.add(ParagraphStyle(name="UniBullet", parent=styles["BodyText"], fontName=NORMAL, fontSize=9.5, leading=13, leftIndent=14, firstLineIndent=-7, bulletIndent=4, spaceAfter=3))

    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm, title=source_name)
    flow = []
    lines = source.read_text(encoding="utf-8").splitlines()
    i = 0
    in_code = False
    code_lines = []

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            if in_code:
                flow.append(Preformatted("\n".join(code_lines), ParagraphStyle(name="Code", fontName="Courier", fontSize=7.5, leading=9.5, backColor=colors.HexColor("#F3F5F7"))))
                flow.append(Spacer(1, 4))
                code_lines = []
            in_code = not in_code
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            flow.append(Paragraph(esc(line[2:].strip()), styles["UniTitle"])); i += 1; continue
        if line.startswith("## "):
            flow.append(Paragraph(esc(line[3:].strip()), styles["UniH1"])); i += 1; continue
        if line.startswith("### "):
            flow.append(Paragraph(esc(line[4:].strip()), styles["UniH2"])); i += 1; continue
        if line.startswith("| "):
            table_lines = []
            while i < len(lines) and lines[i].startswith("| "):
                table_lines.append(lines[i]); i += 1
            table = table_from(table_lines)
            if table:
                flow.append(table); flow.append(Spacer(1, 7))
            continue
        if re.match(r"^- ", line):
            flow.append(Paragraph("• " + esc(line[2:].strip()), styles["UniBullet"])); i += 1; continue
        if re.match(r"^\d+\. ", line):
            flow.append(Paragraph(esc(line), styles["UniBullet"])); i += 1; continue
        flow.append(Paragraph(esc(line), styles["UniBody"])); i += 1

    doc.build(flow, onFirstPage=on_page, onLaterPages=on_page)


if __name__ == "__main__":
    for output_name, source_name in FILES.items():
        build(source_name, output_name)
        print(f"Built {OUT / output_name}")
