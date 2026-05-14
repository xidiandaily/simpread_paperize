"""PDF 页脚模板（标题转义、页码占位）。"""

from paperize.renderer import build_pdf_footer_template


def test_footer_template_escapes_title() -> None:
    html = build_pdf_footer_template('标题含<script>与&符号')
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "pageNumber" in html
    assert "totalPages" in html
    assert "第" in html and "页" in html
    assert "border-top" in html
    assert "text-align:center" in html


def test_footer_template_strips_newlines_in_title() -> None:
    html = build_pdf_footer_template("第一行\n第二行")
    assert "\n" not in html
    assert "第一行" in html
    assert "第二行" in html


def test_footer_empty_title_uses_placeholder() -> None:
    html = build_pdf_footer_template("")
    assert "无标题" in html
