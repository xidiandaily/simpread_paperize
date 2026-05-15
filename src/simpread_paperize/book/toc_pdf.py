"""可打印目录页 PDF（ReportLab）。"""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

# Helvetica 无 CJK 字形，中文会显示为黑块；使用 ReportLab 内置的 Adobe 简体中文 CID 字体。
_CJK_FONT = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(_CJK_FONT))

_TOC_LEFT = 48.0
_TOC_RIGHT = 48.0


def _truncate_to_width(text: str, font: str, size: float, max_width: float) -> str:
    """超出宽度时在末尾加省略号截断。"""
    if max_width <= 0:
        return "…"
    if pdfmetrics.stringWidth(text, font, size) <= max_width:
        return text
    ell = "…"
    if pdfmetrics.stringWidth(ell, font, size) > max_width:
        return ""
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        cand = text[:mid] + ell
        if pdfmetrics.stringWidth(cand, font, size) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ell if lo > 0 else ell


def _draw_toc_entry_line(
    c: canvas.Canvas,
    *,
    y: float,
    title: str,
    start_pg: int,
    page_width: float,
    font: str,
    size: float,
) -> None:
    """一行：左标题（常规体）+ 点线 + 右对齐页码。"""
    left_x = _TOC_LEFT
    right_x = page_width - _TOC_RIGHT
    gap = 6.0
    page_str = str(start_pg)
    page_w = pdfmetrics.stringWidth(page_str, font, size)
    leader_end_x = right_x - page_w - gap
    min_dots_reserve = max(12.0, 3.0 * pdfmetrics.stringWidth(".", font, size))
    max_title_w = max(0.0, leader_end_x - left_x - min_dots_reserve)
    title_disp = _truncate_to_width(title[:800], font, size, max_title_w)
    title_w = pdfmetrics.stringWidth(title_disp, font, size)
    dot = "."
    dot_w = pdfmetrics.stringWidth(dot, font, size)
    leader_available = max(0.0, leader_end_x - left_x - title_w)
    n_dots = max(1, int(leader_available / dot_w)) if dot_w > 0 else 3
    while n_dots > 1 and title_w + n_dots * dot_w > leader_end_x - left_x + 1e-6:
        n_dots -= 1
    leaders = dot * n_dots

    c.setFont(font, size)
    c.drawString(left_x, y, title_disp)
    c.drawString(left_x + title_w, y, leaders)
    c.drawRightString(right_x, y, page_str)


def render_toc_pdf(entries: Iterable[tuple[str, int]], page_size: tuple[float, float] = A4) -> bytes:
    """
    生成单页或多页目录 PDF。

    ``entries``：``(篇名, 该篇在本卷合集中的起始物理页)``；不含封面/目录行。
    """
    buf = BytesIO()
    w, h = page_size
    c = canvas.Canvas(buf, pagesize=page_size)
    c.setTitle("目录")
    c.setFont(_CJK_FONT, 14)
    y = h - 48
    c.drawString(_TOC_LEFT, y, "目录")
    y -= 28
    entry_font = _CJK_FONT
    entry_size = 11
    for title, start_pg in entries:
        if y < 72:
            c.showPage()
            y = h - 48
        _draw_toc_entry_line(
            c,
            y=y,
            title=title,
            start_pg=start_pg,
            page_width=w,
            font=entry_font,
            size=entry_size,
        )
        y -= 16
    c.showPage()
    c.save()
    return buf.getvalue()


def render_overlay_page(
    width_pt: float,
    height_pt: float,
    header: str,
    cur_page: int,
    total_pages: int,
) -> bytes:
    """透明底叠字：居中页眉 + 眉下分隔线；左下角页码（不画页脚线，正文 PDF 常自带）。"""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width_pt, height_pt))
    margin = 36.0
    c.setStrokeGray(0.45)
    c.setLineWidth(0.4)

    c.setFont(_CJK_FONT, 8)
    text = header[:200]
    header_baseline = height_pt - 20.0
    c.drawCentredString(width_pt / 2, header_baseline, text)
    header_rule_y = height_pt - 26.0
    c.line(margin, header_rule_y, width_pt - margin, header_rule_y)

    c.setFont("Helvetica", 8)
    c.drawString(margin, 14.0, f"{cur_page}/{total_pages}")
    c.showPage()
    c.save()
    return buf.getvalue()
