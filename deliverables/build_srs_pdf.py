#!/usr/bin/env python3
"""Build deliverables/UniNest_SRS.pdf from the Markdown source.

The Markdown file is the source of truth. This script parses the subset of
Markdown used in UniNest_SRS.md, builds the academic front matter (cover,
declaration, document control, table of contents) and renders the five Mermaid
diagrams as vector figures with ReportLab.

Usage:
    python3 deliverables/build_srs_pdf.py
"""

from __future__ import annotations

import html
import math
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "UniNest_SRS.md"
OUTPUT = HERE / "UniNest_SRS.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

PAGE_W, PAGE_H = A4
LAND_W, LAND_H = landscape(A4)
MARGIN_L = MARGIN_R = 56.7
MARGIN_T = 72
MARGIN_B = 64
FRAME_W = PAGE_W - MARGIN_L - MARGIN_R
BODY_H = PAGE_H - MARGIN_T - MARGIN_B
LAND_MARGIN = 42
LAND_FRAME_W = LAND_W - 2 * LAND_MARGIN
LAND_FRAME_H = LAND_H - 56 - 48

NAVY = colors.HexColor("#1F3864")
BLUE = colors.HexColor("#2E75B6")
STEEL = colors.HexColor("#5B7DB1")
LIGHT = colors.HexColor("#EAF1FB")
PALE = colors.HexColor("#F5F7FB")
GRID = colors.HexColor("#B4C6E7")
GREY = colors.HexColor("#6B6B6B")
TEXT = colors.HexColor("#1A1A1A")
WHITE = colors.white


# ---------------------------------------------------------------------------
# Fonts and styles
# ---------------------------------------------------------------------------


def register_fonts() -> None:
    files = {
        "DejaVuSerif": "DejaVuSerif.ttf",
        "DejaVuSerif-Bold": "DejaVuSerif-Bold.ttf",
        "DejaVuSerif-Italic": "DejaVuSerif-Italic.ttf",
        "DejaVuSerif-BoldItalic": "DejaVuSerif-BoldItalic.ttf",
        "DejaVuSans": "DejaVuSans.ttf",
        "DejaVuSans-Bold": "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique": "DejaVuSans-Oblique.ttf",
        "DejaVuSans-BoldOblique": "DejaVuSans-BoldOblique.ttf",
        "DejaVuSansMono": "DejaVuSansMono.ttf",
        "DejaVuSansMono-Bold": "DejaVuSansMono-Bold.ttf",
    }
    for name, filename in files.items():
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
    pdfmetrics.registerFontFamily(
        "DejaVuSerif",
        normal="DejaVuSerif",
        bold="DejaVuSerif-Bold",
        italic="DejaVuSerif-Italic",
        boldItalic="DejaVuSerif-BoldItalic",
    )
    pdfmetrics.registerFontFamily(
        "DejaVuSans",
        normal="DejaVuSans",
        bold="DejaVuSans-Bold",
        italic="DejaVuSans-Oblique",
        boldItalic="DejaVuSans-BoldOblique",
    )
    pdfmetrics.registerFontFamily(
        "DejaVuSansMono",
        normal="DejaVuSansMono",
        bold="DejaVuSansMono-Bold",
        italic="DejaVuSansMono",
        boldItalic="DejaVuSansMono-Bold",
    )


def build_styles() -> dict[str, ParagraphStyle]:
    body = ParagraphStyle(
        "Body",
        fontName="DejaVuSerif",
        fontSize=10.4,
        leading=15.2,
        alignment=TA_JUSTIFY,
        spaceBefore=0,
        spaceAfter=6,
        textColor=TEXT,
    )
    bullet = ParagraphStyle(
        "Bullet",
        fontName="DejaVuSerif",
        fontSize=10.1,
        leading=14.4,
        alignment=TA_LEFT,
        leftIndent=16,
        bulletIndent=4,
        bulletFontName="DejaVuSans",
        bulletFontSize=8.5,
        spaceBefore=0,
        spaceAfter=3.2,
        textColor=TEXT,
    )
    table_head = ParagraphStyle(
        "TableHead",
        fontName="DejaVuSans-Bold",
        fontSize=8.2,
        leading=9.8,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
    )
    table_data = ParagraphStyle(
        "TableData",
        fontName="DejaVuSans",
        fontSize=8.2,
        leading=9.8,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
    )
    return {
        "Body": body,
        "BodyLeft": ParagraphStyle("BodyLeft", parent=body, alignment=TA_LEFT),
        "H1": ParagraphStyle(
            "H1",
            fontName="DejaVuSans-Bold",
            fontSize=17,
            leading=21,
            textColor=NAVY,
            spaceBefore=0,
            spaceAfter=4,
            keepWithNext=1,
        ),
        "H2": ParagraphStyle(
            "H2",
            fontName="DejaVuSans-Bold",
            fontSize=12.5,
            leading=16,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=1,
        ),
        "H3": ParagraphStyle(
            "H3",
            fontName="DejaVuSans-Bold",
            fontSize=10.7,
            leading=14,
            textColor=colors.HexColor("#2F5597"),
            spaceBefore=9,
            spaceAfter=3,
            keepWithNext=1,
        ),
        "Bullet": bullet,
        "Number": ParagraphStyle(
            "Number",
            parent=bullet,
            leftIndent=20,
            bulletIndent=4,
        ),
        "TableHead": table_head,
        "TableData": table_data,
        "Caption": ParagraphStyle(
            "Caption",
            fontName="DejaVuSans-Oblique",
            fontSize=9.0,
            leading=12.5,
            alignment=TA_CENTER,
            textColor=GREY,
            spaceBefore=3,
            spaceAfter=12,
        ),
        "Code": ParagraphStyle(
            "Code",
            fontName="DejaVuSansMono",
            fontSize=8.2,
            leading=10.5,
            textColor=TEXT,
            backColor=PALE,
            borderColor=GRID,
            borderWidth=0.5,
            borderPadding=5,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "FrontTitle": ParagraphStyle(
            "FrontTitle",
            fontName="DejaVuSans-Bold",
            fontSize=20,
            leading=24,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=4,
        ),
        "FrontH2": ParagraphStyle(
            "FrontH2",
            fontName="DejaVuSans-Bold",
            fontSize=11.5,
            leading=15,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=1,
        ),
        "FrontBody": ParagraphStyle(
            "FrontBody",
            fontName="DejaVuSerif",
            fontSize=10.6,
            leading=16.5,
            textColor=TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "CoverKicker": ParagraphStyle(
            "CoverKicker",
            fontName="DejaVuSans-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#44546A"),
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            fontName="DejaVuSans-Bold",
            fontSize=40,
            leading=46,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName="DejaVuSerif-Italic",
            fontSize=15,
            leading=19,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "CoverDocType": ParagraphStyle(
            "CoverDocType",
            fontName="DejaVuSans-Bold",
            fontSize=12.5,
            leading=16,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "CoverVersion": ParagraphStyle(
            "CoverVersion",
            fontName="DejaVuSans",
            fontSize=9.5,
            leading=13,
            textColor=GREY,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "CoverMetaLabel": ParagraphStyle(
            "CoverMetaLabel",
            fontName="DejaVuSans-Bold",
            fontSize=9,
            leading=12,
            textColor=NAVY,
            alignment=TA_LEFT,
        ),
        "CoverMetaValue": ParagraphStyle(
            "CoverMetaValue",
            fontName="DejaVuSerif",
            fontSize=10,
            leading=13,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "CoverNote": ParagraphStyle(
            "CoverNote",
            fontName="DejaVuSerif-Italic",
            fontSize=9.5,
            leading=14,
            textColor=GREY,
            alignment=TA_CENTER,
        ),
        "CoverDept": ParagraphStyle(
            "CoverDept",
            fontName="DejaVuSans-Bold",
            fontSize=9.5,
            leading=13,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "SignLabel": ParagraphStyle(
            "SignLabel",
            fontName="DejaVuSans",
            fontSize=8.5,
            leading=11,
            textColor=GREY,
            alignment=TA_LEFT,
        ),
        "SignName": ParagraphStyle(
            "SignName",
            fontName="DejaVuSans-Bold",
            fontSize=9.5,
            leading=13,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "TOC0": ParagraphStyle(
            "TOC0",
            fontName="DejaVuSans-Bold",
            fontSize=10.2,
            leading=15,
            textColor=NAVY,
            spaceBefore=6,
        ),
        "TOC1": ParagraphStyle(
            "TOC1",
            fontName="DejaVuSans",
            fontSize=9.0,
            leading=12.5,
            textColor=TEXT,
            leftIndent=16,
            spaceBefore=0.5,
        ),
    }


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

_CODE_SPAN = re.compile(r"`([^`]+)`")


def inline_markup(text: str) -> str:
    """Convert the inline Markdown used in the SRS into ReportLab markup."""
    code_bits: list[str] = []

    def stash(match: re.Match[str]) -> str:
        code_bits.append(match.group(1))
        return f"\x00C{len(code_bits) - 1}\x00"

    text = _CODE_SPAN.sub(stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    for index, code in enumerate(code_bits):
        replacement = (
            '<font name="DejaVuSansMono" size="9" color="#8B1A1A">%s</font>'
            % html.escape(code, quote=False)
        )
        text = text.replace(f"\x00C{index}\x00", replacement)
    return text


def plain_text(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    return text


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, text[match.end():]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell.strip()) for cell in cells)


def table_col_widths(rows: list[list[str]], available: float,
                     font_size: float = 8.2) -> list[float]:
    ncols = len(rows[0])
    weights: list[float] = []
    minimums: list[float] = []
    for cidx in range(ncols):
        cells = [plain_text(row[cidx]) if cidx < len(row) else "" for row in rows]
        lengths = [len(cell) for cell in cells]
        average = sum(lengths) / max(1, len(lengths))
        longest = max(lengths) if lengths else 1
        weights.append(max(8.0, min(average, 30.0) + min(longest, 60) * 0.20))
        longest_word = max(
            (stringWidth(word, "DejaVuSans", font_size) for cell in cells for word in cell.split()),
            default=8.0,
        )
        minimums.append(min(max(28.0, longest_word + 8.0), 130.0))

    if sum(minimums) > available:
        scale = available / sum(minimums)
        minimums = [value * scale for value in minimums]

    total = sum(weights) or 1.0
    widths = [available * weight / total for weight in weights]
    widths = [max(width, minimums[index]) for index, width in enumerate(widths)]

    while sum(widths) > available:
        excess = sum(widths) - available
        adjustable = [
            index for index, width in enumerate(widths)
            if width > minimums[index] + 0.5
        ]
        if not adjustable:
            break
        pool = sum(widths[index] - minimums[index] for index in adjustable)
        for index in adjustable:
            widths[index] -= excess * (widths[index] - minimums[index]) / pool
    remaining = available - sum(widths)
    if remaining > 0:
        widths = [width + remaining / ncols for width in widths]
    return widths


def make_table(
    rows: list[list[str]],
    styles: dict[str, ParagraphStyle],
    available: float = FRAME_W,
) -> Table:
    ncols = len(rows[0])
    if ncols >= 7:
        size, leading = 7.2, 9.0
    elif ncols >= 5:
        size, leading = 7.8, 9.8
    else:
        size, leading = 8.4, 10.6

    head_style = ParagraphStyle(
        f"TableHead{ncols}",
        parent=styles["TableHead"],
        fontSize=size,
        leading=leading,
    )
    data_style = ParagraphStyle(
        f"TableData{ncols}",
        parent=styles["TableData"],
        fontSize=size,
        leading=leading,
    )
    data = [[Paragraph(inline_markup(cell), head_style) for cell in rows[0]]]
    for row in rows[1:]:
        data.append([Paragraph(inline_markup(cell), data_style) for cell in row])
    widths = table_col_widths(rows, available, size)
    table = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for index in range(1, len(data)):
        if index % 2 == 0:
            commands.append(("BACKGROUND", (0, index), (-1, index), PALE))
    table.setStyle(TableStyle(commands))
    return table


def simple_table(
    rows: list[list[str]],
    styles: dict[str, ParagraphStyle],
    header: bool = True,
    col_widths: list[float] | None = None,
    first_col_bold: bool = False,
) -> Table:
    front_head = ParagraphStyle(
        "FrontTableHead",
        parent=styles["TableHead"],
        fontSize=8.6,
        leading=10.5,
    )
    front_data = ParagraphStyle(
        "FrontTableData",
        parent=styles["TableData"],
        fontSize=8.8,
        leading=11.2,
    )
    front_label = ParagraphStyle(
        "FrontTableLabel",
        parent=front_data,
        fontName="DejaVuSans-Bold",
        textColor=NAVY,
    )
    data = []
    for ridx, row in enumerate(rows):
        cells = []
        for cidx, cell in enumerate(row):
            if header and ridx == 0:
                style = front_head
            elif first_col_bold and cidx == 0:
                style = front_label
            else:
                style = front_data
            cells.append(Paragraph(inline_markup(cell), style))
        data.append(cells)
    if col_widths is None:
        col_widths = table_col_widths(rows, FRAME_W, 8.8)
    table = Table(
        data,
        colWidths=col_widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        for index in range(1, len(data)):
            if index % 2 == 0:
                commands.append(("BACKGROUND", (0, index), (-1, index), PALE))
    table.setStyle(TableStyle(commands))
    return table


def caption_flowable(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    body = text.strip()
    if body.startswith("*") and body.endswith("*"):
        body = body[1:-1]
    return Paragraph(inline_markup(body), styles["Caption"])


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def _draw_lines(
    canvas,
    lines: list[str],
    x: float,
    y_top: float,
    font: str,
    size: float,
    leading: float,
    color=NAVY,
    align: str = "center",
) -> None:
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    y = y_top
    for line in lines:
        if align == "center":
            canvas.drawCentredString(x, y, line)
        elif align == "right":
            canvas.drawRightString(x, y, line)
        else:
            canvas.drawString(x, y, line)
        y -= leading


def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    return simpleSplit(text, font, size, max_width)


def _rounded_box(
    canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[str],
    fill=LIGHT,
    stroke=BLUE,
    font: str = "DejaVuSans-Bold",
    size: float = 8.0,
    leading: float | None = None,
    text_color=NAVY,
    radius: float = 4.0,
    line_width: float = 0.9,
) -> None:
    leading = leading or size * 1.22
    canvas.setFillColor(fill)
    canvas.setStrokeColor(stroke)
    canvas.setLineWidth(line_width)
    canvas.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    top = y + h / 2 + (len(lines) - 1) * leading / 2 - size * 0.32
    _draw_lines(canvas, lines, x + w / 2, top, font, size, leading, text_color)


def _arrow(
    canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color=BLUE,
    width: float = 0.9,
    dash=None,
    head: float = 4.5,
) -> None:
    canvas.saveState()
    canvas.setStrokeColor(color)
    canvas.setFillColor(color)
    canvas.setLineWidth(width)
    canvas.setDash(dash or [])
    canvas.line(x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2, y2)
    p2 = (x2 - head * math.cos(angle - 0.42), y2 - head * math.sin(angle - 0.42))
    p3 = (x2 - head * math.cos(angle + 0.42), y2 - head * math.sin(angle + 0.42))
    canvas.setDash([])
    path = canvas.beginPath()
    path.moveTo(*p1)
    path.lineTo(*p2)
    path.lineTo(*p3)
    path.close()
    canvas.drawPath(path, stroke=0, fill=1)
    canvas.restoreState()


def _polyline(canvas, points: list[tuple[float, float]], color=BLUE,
              width: float = 0.9, dash=None) -> None:
    canvas.saveState()
    canvas.setStrokeColor(color)
    canvas.setLineWidth(width)
    canvas.setDash(dash or [])
    path = canvas.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    canvas.drawPath(path, stroke=1, fill=0)
    canvas.restoreState()


def _poly_arrow(canvas, points: list[tuple[float, float]], **kwargs) -> None:
    if len(points) > 2:
        line_kwargs = {key: value for key, value in kwargs.items() if key != "head"}
        _polyline(canvas, points[:-1], **line_kwargs)
    _arrow(canvas, points[-2][0], points[-2][1], points[-1][0], points[-1][1], **kwargs)


def _label(canvas, text: str, x: float, y: float, size: float = 6.6,
           color=NAVY, font: str = "DejaVuSans-Bold", align: str = "center") -> None:
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    if align == "center":
        canvas.drawCentredString(x, y, text)
    elif align == "right":
        canvas.drawRightString(x, y, text)
    else:
        canvas.drawString(x, y, text)


def _label_block(canvas, lines: list[str], cx: float, top_y: float,
                 font: str, size: float, leading: float, color=NAVY,
                 padding: float = 3.0) -> None:
    widths = [stringWidth(line, font, size) for line in lines]
    width = max(widths, default=8.0) + 2 * padding
    height = (len(lines) - 1) * leading + size + 2 * padding
    x = cx - width / 2
    y = top_y - (len(lines) - 1) * leading - size * 0.35 - padding
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(WHITE)
    canvas.roundRect(x, y, width, height, 2, stroke=0, fill=1)
    _draw_lines(canvas, lines, cx, top_y, font, size, leading, color)


def _actor(canvas, cx: float, cy: float, label: str) -> None:
    canvas.saveState()
    canvas.setStrokeColor(NAVY)
    canvas.setFillColor(WHITE)
    canvas.setLineWidth(1.0)
    canvas.circle(cx, cy + 22, 5.5, stroke=1, fill=1)
    canvas.line(cx, cy + 16.5, cx, cy)
    canvas.line(cx - 10, cy + 8, cx + 10, cy + 8)
    canvas.line(cx, cy, cx - 8, cy - 14)
    canvas.line(cx, cy, cx + 8, cy - 14)
    canvas.setFont("DejaVuSans-Bold", 8)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(cx, cy - 28, label)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Vector diagrams (equivalent to the Mermaid source)
# ---------------------------------------------------------------------------


class Diagram(Flowable):
    HEIGHTS = {
        "workflow": 310,
        "use_case": 545,
        "context": 430,
        "erd": 430,
        "states": 380,
    }

    def __init__(self, name: str, width: float) -> None:
        Flowable.__init__(self)
        self.name = name
        self._width = width
        self._height = self.HEIGHTS[name]

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self._width = min(self._width, availWidth)
        return self._width, self._height

    def draw(self) -> None:
        canvas = self.canv
        canvas.saveState()
        drawer = {
            "workflow": draw_workflow,
            "use_case": draw_use_case,
            "context": draw_context,
            "erd": draw_erd,
            "states": draw_state_model,
        }[self.name]
        drawer(canvas, self._width, self._height)
        canvas.restoreState()


def draw_workflow(canvas, width: float, height: float) -> None:
    steps = [
        "1. Registration",
        "2. Verification",
        "3. Application",
        "4. Review",
        "5. Allocation",
        "6. Payment",
        "7. Confirmation",
        "8. Check-in",
        "9. Check-out",
    ]
    box_w, box_h, gap = 130, 46, 20
    x0 = (width - (3 * box_w + 2 * gap)) / 2
    row_tops = [height - 42, height - 132, height - 222]
    positions: dict[int, tuple[float, float]] = {}

    order = [
        [0, 1, 2],
        [5, 4, 3],
        [6, 7, 8],
    ]
    for row_index, row in enumerate(order):
        top = row_tops[row_index]
        for col_index, step_index in enumerate(row):
            x = x0 + col_index * (box_w + gap)
            y = top - box_h
            positions[step_index] = (x, y)
            _rounded_box(canvas, x, y, box_w, box_h, [steps[step_index]], size=8.2)

    centers = {i: (x + box_w / 2, y + box_h / 2) for i, (x, y) in positions.items()}

    for first, second in [(0, 1), (1, 2), (4, 5), (6, 7), (7, 8)]:
        ax, ay = centers[first]
        bx, by = centers[second]
        if abs(ay - by) < 0.1:
            if bx > ax:
                _arrow(canvas, ax + box_w / 2, ay, bx - box_w / 2, by)
            else:
                _arrow(canvas, ax - box_w / 2, ay, bx + box_w / 2, by)

    x_right = x0 + 2 * (box_w + gap) + box_w / 2
    _arrow(canvas, x_right, row_tops[0] - box_h, x_right, row_tops[1])
    x_left = x0 + box_w / 2
    _arrow(canvas, x_left, row_tops[1] - box_h, x_left, row_tops[2])

    rejected_x = x_right + 18
    _arrow(
        canvas,
        rejected_x,
        row_tops[1],
        rejected_x,
        row_tops[0] - box_h,
        color=STEEL,
        dash=(2, 2),
    )
    _label(canvas, "Rejected", rejected_x + 4,
           (row_tops[0] - box_h + row_tops[1]) / 2, size=6.4,
           color=STEEL, align="left")

    row_two_bottom = row_tops[1] - box_h
    cancel_y = row_two_bottom - 16
    x_alloc = positions[4][0] + box_w / 2
    x_review = positions[3][0] + box_w / 2
    _poly_arrow(
        canvas,
        [
            (x_alloc, row_two_bottom),
            (x_alloc, cancel_y),
            (x_review, cancel_y),
            (x_review, row_two_bottom),
        ],
        color=STEEL,
        dash=(2, 2),
    )
    _label(canvas, "Cancelled", (x_alloc + x_review) / 2, cancel_y - 9,
           size=6.4, color=STEEL)


def draw_use_case(canvas, width: float, height: float) -> None:
    boundary_x, boundary_y = 188, 26
    boundary_w, boundary_h = 292, height - 52
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#FBFCFE"))
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.8)
    canvas.setDash(3, 3)
    canvas.roundRect(boundary_x, boundary_y, boundary_w, boundary_h, 10, stroke=1, fill=1)
    canvas.setDash([])
    canvas.setFont("DejaVuSans-Bold", 8.5)
    canvas.setFillColor(STEEL)
    canvas.drawString(boundary_x + 10, boundary_y + boundary_h - 14,
                      "UniNest system boundary")
    canvas.restoreState()

    rows = [
        (1, ["Register / Login"]),
        (2, ["Apply for Hostel"]),
        (3, ["Record Payment"]),
        (4, ["Submit Maintenance"]),
        (5, ["Verify Students"]),
        (6, ["Manage Hostels,", "Rooms and Beds"]),
        (7, ["Review Application"]),
        (8, ["Allocate Bed and", "Record Residence"]),
        (9, ["Confirm Payments"]),
        (10, ["View Reports and", "Monitor Occupancy"]),
    ]
    center_x = 334
    top_y = height - 62
    spacing = 44
    centers = {
        number: (center_x, top_y - index * spacing)
        for index, (number, _lines) in enumerate(rows)
    }
    ellipse_w, ellipse_h = 168, 38

    actors = [
        (62, 380, "Student", [1, 2, 3, 4], BLUE),
        (62, 226, "Administrator", [1, 5, 6, 7, 8, 9, 10], NAVY),
        (62, 82, "Management", [1, 10], colors.HexColor("#555555")),
    ]

    for actor_x, actor_y, _name, links, color in actors:
        for number in links:
            use_x, use_y = centers[number]
            _arrow(
                canvas,
                actor_x + 13,
                actor_y + 4,
                use_x - ellipse_w / 2 + 2,
                use_y,
                color=color,
                width=0.75,
                head=3.2,
            )

    for number, lines in rows:
        use_x, use_y = centers[number]
        canvas.setFillColor(PALE)
        canvas.setStrokeColor(BLUE)
        canvas.setLineWidth(0.9)
        canvas.ellipse(
            use_x - ellipse_w / 2,
            use_y - ellipse_h / 2,
            use_x + ellipse_w / 2,
            use_y + ellipse_h / 2,
            stroke=1,
            fill=1,
        )
        _draw_lines(canvas, lines, use_x, use_y + (len(lines) - 1) * 4.4 - 2.5,
                    "DejaVuSans", 7.1, 8.8, NAVY)

    for actor_x, actor_y, name, _links, _color in actors:
        _actor(canvas, actor_x, actor_y, name)

    _label(
        canvas,
        "Links: student (blue)  ·  administrator (navy)  ·  management (grey)",
        boundary_x + 12, boundary_y + 12, size=6.4, color=GREY,
        font="DejaVuSans", align="left",
    )


def draw_context(canvas, width: float, height: float) -> None:
    process_x, process_y, process_w, process_h = 298, 188, 154, 82
    canvas.setFillColor(NAVY)
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(1.0)
    canvas.roundRect(process_x, process_y, process_w, process_h, 8, stroke=1, fill=1)
    _draw_lines(
        canvas,
        ["UniNest", "Hostel Management System"],
        process_x + process_w / 2,
        process_y + process_h / 2 + 2,
        "DejaVuSans-Bold",
        8.6,
        11,
        WHITE,
    )

    entities = [
        (20, 320, 120, 44, "Student"),
        (20, 210, 120, 44, "Hostel Administrator"),
        (20, 100, 120, 44, "University Management"),
    ]
    for x, y, w, h, label in entities:
        _rounded_box(canvas, x, y, w, h, [label], size=8.0, fill=LIGHT)

    flows = [
        ((140, 342), (process_x, 252), "registration, profile, application, payment record, maintenance request", BLUE, (214, 318)),
        ((process_x, 232), (140, 320), "status, allocation, payment confirmation, notifications", STEEL, (214, 268)),
        ((140, 232), (process_x, 228), "verification, review, allocation, payment decision, maintenance, inventory", BLUE, (214, 246)),
        ((process_x, 208), (140, 210), "pending queues, availability, payment details, reports", STEEL, (214, 198)),
        ((140, 122), (process_x, 198), "report requests", BLUE, (214, 162)),
        ((process_x, 178), (140, 100), "occupancy, vacancy, payment and allocation reports", STEEL, (214, 112)),
    ]
    for (x1, y1), (x2, y2), text, color, (lx, ly) in flows:
        _arrow(
            canvas,
            x1,
            y1,
            x2,
            y2,
            color=color,
            dash=None if color is BLUE else (3, 2),
        )
        lines = _wrap(text, "DejaVuSans", 6.7, 152)
        _label_block(canvas, lines, lx, ly, "DejaVuSans", 6.7, 8.0, color)

    _label(canvas, "External entities", 20, 44, size=7.5, color=GREY,
           font="DejaVuSans-Bold", align="left")
    _label(canvas, "solid arrows = data into UniNest   ·   dashed arrows = data out",
           20, 30, size=6.4, color=GREY, font="DejaVuSans", align="left")


def _entity_box(canvas, x: float, y: float, w: float, h: float,
                name: str, fields: list[str]) -> None:
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.7)
    canvas.rect(x, y, w, h, stroke=1, fill=1)
    canvas.setFillColor(NAVY)
    canvas.rect(x, y + h - 16, w, 16, stroke=0, fill=1)
    canvas.setFillColor(WHITE)
    canvas.setFont("DejaVuSans-Bold", 7.2)
    canvas.drawCentredString(x + w / 2, y + h - 11, name)
    canvas.setFont("DejaVuSans", 6.3)
    canvas.setFillColor(TEXT)
    for index, field in enumerate(fields[:3]):
        canvas.drawString(x + 5, y + h - 28 - index * 11, field)


def _erd_line(canvas, points: list[tuple[float, float]], label_left: str,
              label_right: str, left_at: tuple[float, float],
              right_at: tuple[float, float]) -> None:
    _poly_arrow(canvas, points, color=STEEL, width=0.75, head=4.0)
    _label(canvas, label_left, left_at[0], left_at[1], size=6.4, color=NAVY)
    _label(canvas, label_right, right_at[0], right_at[1], size=6.4, color=NAVY)


def draw_erd(canvas, width: float, height: float) -> None:
    entities = {
        "users": (30, 350, ["PK  id", "email", "role"]),
        "students": (210, 350, ["PK  id", "FK  user_id", "registration_no"]),
        "applications": (400, 355, ["PK  id", "FK  student_id", "status"]),
        "allocations": (590, 350, ["PK  id", "FK  student_id", "FK  bed_id"]),
        "notifications": (30, 230, ["PK  id", "FK  user_id", "is_read"]),
        "hostels": (210, 220, ["PK  id", "name", "gender"]),
        "rooms": (400, 240, ["PK  id", "FK  hostel_id", "number"]),
        "beds": (590, 230, ["PK  id", "FK  room_id", "status"]),
        "payments": (400, 90, ["PK  id", "FK  student_id", "status"]),
        "maintenance_requests": (590, 90, ["PK  id", "FK  student_id", "status"]),
    }
    box_w, box_h = 142, 62

    _erd_line(canvas, [(172, 380), (210, 380)], "1", "0..1", (178, 385), (192, 385))
    _erd_line(canvas, [(101, 350), (101, 292)], "1", "N", (106, 332), (106, 300))
    _erd_line(canvas, [(352, 385), (400, 388)], "1", "N", (361, 390), (391, 393))
    _erd_line(canvas, [(542, 390), (590, 380)], "1", "N", (550, 395), (580, 385))
    _erd_line(canvas, [(352, 250), (400, 255)], "1", "N", (362, 255), (390, 260))
    _erd_line(canvas, [(542, 270), (590, 260)], "1", "N", (552, 275), (580, 265))
    _erd_line(canvas, [(661, 292), (661, 350)], "N", "1", (666, 302), (666, 340))
    _erd_line(canvas, [(352, 238), (400, 370)], "1", "N", (358, 250), (391, 360))
    _erd_line(
        canvas,
        [(281, 350), (281, 330), (575, 330), (575, 380), (590, 380)],
        "1", "N", (286, 340), (580, 385),
    )
    _erd_line(
        canvas,
        [(210, 370), (190, 370), (190, 120), (400, 120)],
        "1", "N", (195, 376), (390, 126),
    )
    _erd_line(
        canvas,
        [(590, 370), (570, 370), (570, 120), (542, 120)],
        "1", "N", (575, 376), (550, 126),
    )
    _erd_line(
        canvas,
        [(732, 370), (748, 370), (748, 120), (732, 120)],
        "1", "N", (737, 376), (737, 126),
    )
    _erd_line(
        canvas,
        [(210, 360), (180, 360), (180, 60), (661, 60), (661, 90)],
        "1", "N", (185, 366), (666, 74),
    )

    for name, (x, y, fields) in entities.items():
        _entity_box(canvas, x, y, box_w, box_h, name, fields)

    _label(
        canvas,
        "PK = primary key   ·   FK = foreign key   ·   1 / N = cardinality   ·   0..1 = optional one",
        30, 22, size=6.4, color=GREY, font="DejaVuSans", align="left",
    )


def _state_box(canvas, cx: float, cy: float, text: str,
               w: float = 92, h: float = 34) -> tuple[float, float, float, float]:
    x, y = cx - w / 2, cy - h / 2
    _rounded_box(canvas, x, y, w, h, [text], size=7.5, fill=LIGHT, stroke=BLUE)
    return x, y, w, h


def _end_state(canvas, x: float, y: float) -> None:
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(0.9)
    canvas.circle(x, y, 5.5, stroke=1, fill=1)
    canvas.setFillColor(NAVY)
    canvas.circle(x, y, 3.2, stroke=0, fill=1)


def draw_state_model(canvas, width: float, height: float) -> None:
    pending = (85, 330)
    review = (215, 330)
    approved = (340, 330)
    rejected = (215, 250)
    allocated = (340, 250)
    checked_in = (340, 170)
    checked_out = (215, 170)
    cancelled = (440, 250)

    for center, label in [
        (pending, "Pending"),
        (review, "UnderReview"),
        (approved, "Approved"),
        (rejected, "Rejected"),
        (allocated, "Allocated"),
        (checked_in, "CheckedIn"),
        (checked_out, "CheckedOut"),
        (cancelled, "Cancelled"),
    ]:
        _state_box(canvas, center[0], center[1], label,
                   w=80 if center == cancelled else 92)

    canvas.setFillColor(NAVY)
    canvas.circle(26, 330, 3.6, stroke=0, fill=1)
    _arrow(canvas, 30, 330, 39, 330)

    _arrow(canvas, 131, 330, 169, 330)
    _label(canvas, "review", 150, 336, size=6.0, color=STEEL, font="DejaVuSans")

    _arrow(canvas, 261, 330, 294, 330)
    _label(canvas, "approve", 277, 336, size=6.0, color=STEEL, font="DejaVuSans")

    _arrow(canvas, 215, 313, 215, 267)
    _label(canvas, "reject", 220, 292, size=6.0, color=STEEL,
           font="DejaVuSans", align="left")

    _arrow(canvas, 340, 313, 340, 267)
    _label(canvas, "allocate", 345, 292, size=6.0, color=STEEL,
           font="DejaVuSans", align="left")

    _arrow(canvas, 340, 233, 340, 187)
    _label(canvas, "check in", 345, 212, size=6.0, color=STEEL,
           font="DejaVuSans", align="left")

    _arrow(canvas, 294, 170, 261, 170)
    _label(canvas, "check out", 277, 176, size=6.0, color=STEEL,
           font="DejaVuSans")

    _arrow(canvas, 386, 250, 400, 250)
    _label(canvas, "cancel", 393, 256, size=6.0, color=STEEL,
           font="DejaVuSans")

    _poly_arrow(
        canvas,
        [(386, 170), (440, 170), (440, 233)],
        color=STEEL,
        width=0.85,
    )
    _label(canvas, "cancel", 444, 180, size=6.0, color=STEEL,
           font="DejaVuSans", align="left")

    _poly_arrow(
        canvas,
        [(440, 267), (440, 292), (396, 292), (396, 330), (386, 330)],
        color=STEEL,
        width=0.85,
        dash=(2, 2),
    )
    _label(canvas, "reopen", 418, 296, size=6.0, color=STEEL,
           font="DejaVuSans")

    _arrow(canvas, 169, 250, 143, 250)
    _end_state(canvas, 137, 250)

    _arrow(canvas, 169, 170, 143, 170)
    _end_state(canvas, 137, 170)

    _label(
        canvas,
        "Payment: pending → confirmed or failed    ·    Maintenance: submitted → in_progress → resolved",
        width / 2, 42, size=6.8, color=GREY, font="DejaVuSans",
    )
    _label(
        canvas,
        "Dashed transition: cancelled allocation returns the application to approved",
        width / 2, 28, size=6.4, color=GREY, font="DejaVuSans",
    )


# ---------------------------------------------------------------------------
# Front matter
# ---------------------------------------------------------------------------


def cover_story(meta: dict[str, str], styles: dict[str, ParagraphStyle]) -> list:
    story: list = []
    story.append(HRFlowable(width="100%", thickness=8, color=NAVY,
                            spaceBefore=0, spaceAfter=0))
    story.append(Spacer(1, 26))
    story.append(Paragraph("DEPARTMENT OF INFORMATION TECHNOLOGY", styles["CoverKicker"]))
    story.append(Spacer(1, 56))
    story.append(Paragraph(meta.get("title", "UniNest"), styles["CoverTitle"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(meta.get("subtitle", "A University Hostel Management System"),
                           styles["CoverSubtitle"]))
    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=1.2, color=BLUE,
                            spaceBefore=0, spaceAfter=12))
    story.append(Paragraph("SYSTEM REQUIREMENTS SPECIFICATION", styles["CoverDocType"]))
    story.append(Paragraph(
        f"Version {meta.get('version', '2.0')}   ·   {meta.get('date', 'November 2026')}",
        styles["CoverVersion"],
    ))
    story.append(Spacer(1, 44))

    details = [
        ("Prepared by", meta.get("author", "Victor Ndirangu")),
        ("Registration No.", meta.get("registration", "25/03338")),
        ("Programme", meta.get("programme", "Diploma in Information Technology")),
        ("Unit", meta.get("unit", "Programming Project (STU 701)")),
        ("Supervisor", meta.get("supervisor", "Geoffrey Rumbe")),
        ("Department", meta.get("department", "Department of Information Technology")),
    ]
    data = [
        [Paragraph(label, styles["CoverMetaLabel"]),
         Paragraph(inline_markup(value), styles["CoverMetaValue"])]
        for label, value in details
    ]
    table = Table(data, colWidths=[130, 310], hAlign="CENTER")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row in range(len(data) - 1):
        commands.append(("LINEBELOW", (0, row), (-1, row), 0.35, GRID))
    table.setStyle(TableStyle(commands))
    story.append(table)

    story.append(Spacer(1, 34))
    story.append(Paragraph(
        "Submitted in partial fulfilment of the requirements for the "
        "Diploma in Information Technology.",
        styles["CoverNote"],
    ))
    story.append(Spacer(1, 16))
    story.append(Paragraph(meta.get("department", "Department of Information Technology"),
                           styles["CoverDept"]))
    story.append(Paragraph("2026", styles["CoverDept"]))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=3, color=NAVY,
                            spaceBefore=0, spaceAfter=0))
    return story


def _signature_table(styles: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [
            ["", ""],
            [
                Paragraph("Signature", styles["SignLabel"]),
                Paragraph("Date", styles["SignLabel"]),
            ],
        ],
        colWidths=[300, 120],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 0.8, NAVY),
        ("LINEBELOW", (1, 0), (1, 0), 0.8, NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 30),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


def declaration_story(styles: dict[str, ParagraphStyle]) -> list:
    story: list = [
        Paragraph("Declaration", styles["FrontTitle"]),
        HRFlowable(width="100%", thickness=1.2, color=NAVY,
                   spaceBefore=2, spaceAfter=16),
        Paragraph(
            "I, <b>Victor Ndirangu</b> (Registration No. 25/03338), declare that this "
            "System Requirements Specification for <b>UniNest — A University Hostel "
            "Management System</b> is my original work and has not been submitted for "
            "examination in any other institution. All sources of information used "
            "have been acknowledged by means of references.",
            styles["FrontBody"],
        ),
        Paragraph(
            "The requirements documented here were derived from the project proposal, "
            "interviews with hostel staff, a student questionnaire and an inspection of "
            "the implemented UniNest system. The document is submitted in partial "
            "fulfilment of the requirements for the Diploma in Information Technology "
            "(Programming Project STU 701).",
            styles["FrontBody"],
        ),
        Spacer(1, 26),
        _signature_table(styles),
        Spacer(1, 6),
        Paragraph("Victor Ndirangu", styles["SignName"]),
        Paragraph("Student · Registration No. 25/03338", styles["SignLabel"]),
        Spacer(1, 34),
        Paragraph("Supervisor's Approval", styles["FrontH2"]),
        Paragraph(
            "This System Requirements Specification has been submitted for examination "
            "with my approval as the project supervisor.",
            styles["FrontBody"],
        ),
        Spacer(1, 18),
        _signature_table(styles),
        Spacer(1, 6),
        Paragraph("Geoffrey Rumbe", styles["SignName"]),
        Paragraph("Project Supervisor", styles["SignLabel"]),
    ]
    return story


def document_control_story(meta: dict[str, str],
                           styles: dict[str, ParagraphStyle]) -> list:
    story: list = [
        Paragraph("Document Control", styles["FrontTitle"]),
        HRFlowable(width="100%", thickness=1.2, color=NAVY,
                   spaceBefore=2, spaceAfter=12),
        Paragraph("Document identification", styles["FrontH2"]),
    ]
    identification = [
        ["Document title", "UniNest — System Requirements Specification"],
        ["Document version", meta.get("version", "2.0")],
        ["Status", "Final"],
        ["Author", f"{meta.get('author', 'Victor Ndirangu')} "
                   f"({meta.get('registration', '25/03338')})"],
        ["Supervisor", meta.get("supervisor", "Geoffrey Rumbe")],
        ["Date", meta.get("date", "November 2026")],
    ]
    story.append(simple_table(
        identification, styles, header=False, first_col_bold=True,
        col_widths=[125, 357],
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Version history", styles["FrontH2"]))
    versions = [
        ["Version", "Date", "Author", "Description"],
        ["1.0", "2026", "Victor Ndirangu", "Initial requirements draft."],
        ["2.0", "November 2026", "Victor Ndirangu",
         "Guideline-compliant rewrite with expanded functional and non-functional "
         "requirements, system models, data requirements and appendices."],
    ]
    story.append(simple_table(
        versions, styles, header=True,
        col_widths=[50, 82, 100, 250],
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Distribution", styles["FrontH2"]))
    distribution = [
        ["Recipient", "Role", "Purpose"],
        ["Geoffrey Rumbe", "Project supervisor", "Academic supervision and assessment"],
        ["Department of Information Technology", "Examiner", "Project examination"],
        ["Hostel Office", "System owner", "Requirements validation and acceptance"],
        ["University Management", "Stakeholder", "Monitoring and reporting requirements"],
    ]
    story.append(simple_table(
        distribution, styles, header=True,
        col_widths=[150, 120, 212],
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Related documents", styles["FrontH2"]))
    related = [
        ["Document", "Location", "Purpose"],
        ["Revised project proposal", "deliverables/UniNest_Proposal_Revised.md",
         "Project background, objectives, budget and schedule"],
        ["System architecture", "docs/ARCHITECTURE.md",
         "Component structure and data flow"],
        ["User manual", "deliverables/User_Manual.md",
         "Operating instructions for each role"],
        ["Project README", "README.md",
         "Setup, demo accounts and testing commands"],
    ]
    story.append(simple_table(
        related, styles, header=True,
        col_widths=[105, 210, 167],
    ))
    return story


def toc_story(styles: dict[str, ParagraphStyle]) -> list:
    toc = TableOfContents()
    toc.levelStyles = [styles["TOC0"], styles["TOC1"]]
    toc.dotsMinLevel = 0
    return [
        Paragraph("Table of Contents", styles["FrontTitle"]),
        HRFlowable(width="100%", thickness=1.2, color=NAVY,
                   spaceBefore=2, spaceAfter=16),
        toc,
    ]


# ---------------------------------------------------------------------------
# Document template and page furniture
# ---------------------------------------------------------------------------


class SRSDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs) -> None:
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self._heading_counter = 0

    def beforeDocument(self) -> None:
        self._heading_counter = 0

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in ("H1", "H2"):
            return
        level = 0 if style_name == "H1" else 1
        text = flowable.getPlainText()
        self._heading_counter += 1
        key = f"heading-{self._heading_counter}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=(level == 0))
        self.notify("TOCEntry", (level, text, self.page, key))


def _draw_header(canvas, wide: bool = False) -> None:
    width = LAND_W if wide else PAGE_W
    height = LAND_H if wide else PAGE_H
    margin = LAND_MARGIN if wide else MARGIN_L
    canvas.saveState()
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.6)
    canvas.line(margin, height - 50, width - margin, height - 50)
    canvas.setFont("DejaVuSans", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(margin, height - 40, "UniNest — System Requirements Specification")
    canvas.drawRightString(width - margin, height - 40, "Version 2.0")
    canvas.restoreState()


def _cover_page(canvas, doc) -> None:
    canvas._page_template_name = "cover"


def _front_page(canvas, doc) -> None:
    canvas._page_template_name = "front"


def _body_page(canvas, doc) -> None:
    canvas._page_template_name = "body"
    _draw_header(canvas)


def _landscape_page(canvas, doc) -> None:
    canvas._page_template_name = "landscape"
    _draw_header(canvas, wide=True)


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs) -> None:
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states: list[dict] = []
        self._page_template_name = "cover"

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_footer(self, total: int) -> None:
        if getattr(self, "_page_template_name", "cover") == "cover":
            return
        width, _ = self._pagesize
        margin = LAND_MARGIN if width > 700 else MARGIN_L
        self.saveState()
        self.setStrokeColor(GRID)
        self.setLineWidth(0.5)
        self.line(margin, 44, width - margin, 44)
        self.setFont("DejaVuSans", 7.5)
        self.setFillColor(GREY)
        self.drawString(margin, 32, "Victor Ndirangu · 25/03338")
        self.drawCentredString(width / 2, 32, f"Page {self._pageNumber} of {total}")
        self.drawRightString(width - margin, 32, "Department of Information Technology")
        self.restoreState()


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------


def markdown_to_story(text: str,
                      styles: dict[str, ParagraphStyle]) -> tuple[dict[str, str], list]:
    meta, body = parse_front_matter(text)
    body = re.sub(r"<!--\s*pagebreak\s*-->", "\n@@PAGEBREAK@@\n", body, flags=re.I)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    lines = body.splitlines()
    story: list = []
    paragraph: list[str] = []
    first_h1 = True

    def flush_paragraph() -> None:
        if not paragraph:
            return
        value = " ".join(part.strip() for part in paragraph).strip()
        paragraph.clear()
        if value:
            story.append(Paragraph(inline_markup(value), styles["Body"]))

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped == "@@PAGEBREAK@@":
            flush_paragraph()
            story.append(PageBreak())
            i += 1
            continue

        if stripped == "---":
            flush_paragraph()
            story.append(HRFlowable(width="100%", thickness=0.6, color=GRID,
                                    spaceBefore=4, spaceAfter=8))
            i += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                if not first_h1:
                    story.append(PageBreak())
                first_h1 = False
                story.append(Paragraph(inline_markup(title), styles["H1"]))
                story.append(HRFlowable(width="100%", thickness=1.1, color=NAVY,
                                        spaceBefore=2, spaceAfter=10))
            elif level == 2:
                story.append(Paragraph(inline_markup(title), styles["H2"]))
            else:
                story.append(Paragraph(inline_markup(title), styles["H3"]))
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip().lower()
            i += 1
            block: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            if language == "mermaid":
                figure_name = None
                for block_line in block:
                    found = re.search(r"%%\s*figure:\s*([A-Za-z_]+)", block_line)
                    if found:
                        figure_name = found.group(1).lower()
                if figure_name in Diagram.HEIGHTS:
                    caption = None
                    j = i
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and lines[j].strip().startswith("*Figure"):
                        caption = lines[j].strip()
                        i = j + 1
                    if figure_name == "erd":
                        story.append(NextPageTemplate("landscape"))
                        story.append(PageBreak())
                        story.append(Spacer(1, 4))
                        story.append(Diagram("erd", LAND_FRAME_W))
                        if caption:
                            story.append(caption_flowable(caption, styles))
                        story.append(NextPageTemplate("body"))
                        story.append(PageBreak())
                    else:
                        group = [Spacer(1, 4), Diagram(figure_name, FRAME_W)]
                        if caption:
                            group.append(caption_flowable(caption, styles))
                        story.append(KeepTogether(group))
                else:
                    story.append(Paragraph(
                        "Diagram unavailable in the PDF build.",
                        styles["Caption"],
                    ))
            else:
                code = "\n".join(block)
                escaped = html.escape(code, quote=False).replace("\n", "<br/>")
                story.append(Paragraph(escaped, styles["Code"]))
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_line = lines[i].strip()
                cells = [cell.strip() for cell in row_line.strip("|").split("|")]
                rows.append(cells)
                i += 1
            if len(rows) >= 2 and is_separator(rows[1]):
                rows = [rows[0]] + rows[2:]
            if rows:
                ncols = max(len(row) for row in rows)
                rows = [row + [""] * (ncols - len(row)) for row in rows]
                story.append(make_table(rows, styles))
                story.append(Spacer(1, 7))
            continue

        if re.match(r"^(?:[-*]\s+|\d+\.\s+)", stripped):
            flush_paragraph()
            items: list[tuple[str, str, str]] = []
            while i < len(lines):
                item_line = lines[i].strip()
                if not item_line:
                    break
                bullet_match = re.match(r"^(?:([-*])\s+|\d+\.\s+)(.*)$", item_line)
                if not bullet_match:
                    break
                if bullet_match.group(1):
                    items.append(("•", bullet_match.group(2).strip(), "Bullet"))
                else:
                    number = re.match(r"^(\d+)\.", item_line).group(1)
                    items.append((number + ".", bullet_match.group(2).strip(), "Number"))
                i += 1
            for bullet, item_text, style_name in items:
                story.append(Paragraph(
                    inline_markup(item_text),
                    styles[style_name],
                    bulletText=bullet,
                ))
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("*Figure") and stripped.endswith("*"):
            flush_paragraph()
            story.append(caption_flowable(stripped, styles))
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return meta, story


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def make_document(meta: dict[str, str]) -> SRSDocTemplate:
    document = SRSDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title="UniNest — System Requirements Specification",
        author=meta.get("author", "Victor Ndirangu"),
        subject="System Requirements Specification for a University Hostel Management System",
        creator="UniNest SRS build script",
        keywords="UniNest, SRS, hostel management, requirements, Flask",
    )
    cover_frame = Frame(
        MARGIN_L, 56.7, FRAME_W, PAGE_H - 2 * 56.7,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="cover_frame",
    )
    front_frame = Frame(
        MARGIN_L, MARGIN_B, FRAME_W, BODY_H,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="front_frame",
    )
    body_frame = Frame(
        MARGIN_L, MARGIN_B, FRAME_W, BODY_H,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="body_frame",
    )
    landscape_frame = Frame(
        LAND_MARGIN, 48, LAND_FRAME_W, LAND_FRAME_H,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="landscape_frame",
    )
    document.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=_cover_page, pagesize=A4),
        PageTemplate(id="front", frames=[front_frame], onPage=_front_page, pagesize=A4),
        PageTemplate(id="body", frames=[body_frame], onPage=_body_page, pagesize=A4),
        PageTemplate(id="landscape", frames=[landscape_frame],
                     onPage=_landscape_page, pagesize=landscape(A4)),
    ])
    return document


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source file not found: {SOURCE}")
    register_fonts()
    styles = build_styles()
    meta, body_story = markdown_to_story(SOURCE.read_text(encoding="utf-8"), styles)

    story: list = []
    story.extend(cover_story(meta, styles))
    story.extend([NextPageTemplate("front"), PageBreak()])
    story.extend(declaration_story(styles))
    story.append(PageBreak())
    story.extend(document_control_story(meta, styles))
    story.append(PageBreak())
    story.extend(toc_story(styles))
    story.extend([NextPageTemplate("body"), PageBreak()])
    story.extend(body_story)

    document = make_document(meta)
    passes = document.multiBuild(story, canvasmaker=NumberedCanvas)
    print(f"Built {OUTPUT} in {passes} pass(es)")


if __name__ == "__main__":
    main()
