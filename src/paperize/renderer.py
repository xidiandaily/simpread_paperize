"""Playwright 渲染与 PDF 导出。"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from paperize.config import runtime_js_path
from paperize.models import ConvertOptions


def _margin_dict(margin: str) -> dict[str, str]:
    return {"top": margin, "right": margin, "bottom": margin, "left": margin}


def render_pdf(
    cleaned_html_path: Path,
    output_pdf_path: Path,
    options: ConvertOptions,
    css_paths: list[Path],
    log_lines: list[str] | None = None,
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

    margins = _margin_dict(options.margin)
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
                page.pdf(
                    path=str(output_pdf_path),
                    format=fmt,
                    margin=margins,
                    print_background=options.print_background,
                    prefer_css_page_size=options.prefer_css_page_size,
                )
                trace(f"已写入 PDF: {output_pdf_path}")
            finally:
                browser.close()
    except Exception as e:
        trace(f"渲染失败: {type(e).__name__}: {e}")
        raise
