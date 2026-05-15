"""可打印目录页 PDF（ReportLab）。"""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def render_toc_pdf(entries: Iterable[tuple[str, int]], page_size: tuple[float, float] = A4) -> bytes:
    """
    生成单页或多页目录 PDF。

    ``entries``：``(篇名, 该篇在本卷合集中的起始物理页)``；不含封面/目录行。
    """
    buf = BytesIO()
    w, h = page_size
    c = canvas.Canvas(buf, pagesize=page_size)
    c.setTitle("目录")
    c.setFont("Helvetica-Bold", 14)
    y = h - 48
    c.drawString(48, y, "目录")
    y -= 28
    c.setFont("Helvetica", 11)
    for title, start_pg in entries:
        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = h - 48
        line = f"{title} … {start_pg}"
        c.drawString(48, y, line[:120])
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
    """透明底叠字：页眉 + 左下角 当前页/总页数。"""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width_pt, height_pt))
    c.setFont("Helvetica", 8)
    text = header[:200]
    c.drawString(36, height_pt - 22, text)
    c.drawString(36, 14, f"{cur_page}/{total_pages}")
    c.showPage()
    c.save()
    return buf.getvalue()
