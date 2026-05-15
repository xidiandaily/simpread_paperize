"""Playwright 渲染与 PDF 导出。"""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from simpread_paperize.config import runtime_js_path
from simpread_paperize.models import ConvertOptions


def _margin_dict(margin: str, *, bottom: str | None = None) -> dict[str, str]:
    b = bottom if bottom is not None else margin
    return {"top": margin, "right": margin, "bottom": b, "left": margin}


def build_pdf_footer_template(document_title: str) -> str:
    """Chromium `page.pdf` 页脚 HTML；标题会做 HTML 转义。

    与正文之间用顶部分割线分隔；标题在页宽中居中，页码仍右对齐。
    """
    raw = (document_title or "").strip()
    esc = html_lib.escape(re.sub(r"[\r\n]+", " ", raw) or "无标题")
    # 三列表格：左右留白列 + 居中标题 + 右对齐页码；顶边线分隔正文
    return (
        '<div style="width:100%;margin:0;padding:6px 0 0 0;border-top:1px solid #888;'
        "font-size:9pt;line-height:1.35;color:#222;"
        'font-family:PingFang SC,Microsoft YaHei,Hiragino Sans GB,sans-serif;">'
        '<table style="width:100%;border-collapse:collapse;margin:0;">'
        "<tr>"
        '<td style="width:18%;padding:0;"></td>'
        f'<td style="text-align:center;vertical-align:middle;width:64%;padding:0 2mm;">{esc}</td>'
        '<td style="width:18%;text-align:right;vertical-align:middle;white-space:nowrap;padding:0;">'
        '第 <span class="pageNumber"></span> / <span class="totalPages"></span> 页'
        "</td>"
        "</tr>"
        "</table>"
        "</div>"
    )


def render_pdf(
    cleaned_html_path: Path,
    output_pdf_path: Path,
    options: ConvertOptions,
    css_paths: list[Path],
    log_lines: list[str] | None = None,
    *,
    document_title: str = "",
) -> None:
    """将已落盘的 cleaned HTML 渲染为 PDF。失败抛出异常，由上层翻译为中文。"""
    log = log_lines if log_lines is not None else []

    def trace(msg: str) -> None:
        log.append(msg)

    uri = cleaned_html_path.resolve().as_uri()
    trace(f"加载页面: {uri}")

    fmt = "A4" if options.paper.upper() == "A4" else options.paper
    if fmt != "A4":
        raise ValueError(f"暂不支持的纸张: {options.paper}")

    # 页脚占高度：略加大下边距，避免与正文重叠
    margins = _margin_dict(options.margin, bottom="22mm")
    js_path = runtime_js_path()
    if not js_path.is_file():
        raise FileNotFoundError(f"未找到 runtime_patch.js: {js_path}")

    css_contents: list[str] = []
    for p in css_paths:
        if not p.is_file():
            raise FileNotFoundError(f"未找到 CSS: {p}")
        css_contents.append(p.read_text(encoding="utf-8"))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.emulate_media(media="print")
                page.goto(uri, wait_until="domcontentloaded", timeout=60_000)
                for css in css_contents:
                    page.add_style_tag(content=css)
                page.add_script_tag(path=str(js_path))
                page.wait_for_timeout(500)
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    trace("networkidle 等待超时，继续导出。")
                output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                footer_html = build_pdf_footer_template(document_title)
                trace("启用 PDF 页脚（标题 + 页码）。")
                page.pdf(
                    path=str(output_pdf_path),
                    format=fmt,
                    margin=margins,
                    print_background=options.print_background,
                    prefer_css_page_size=options.prefer_css_page_size,
                    display_header_footer=True,
                    header_template='<div style="height:0;margin:0;padding:0;font-size:1px;"></div>',
                    footer_template=footer_html,
                )
                trace(f"已写入 PDF: {output_pdf_path}")
            finally:
                browser.close()
    except Exception as e:
        trace(f"渲染失败: {type(e).__name__}: {e}")
        raise
