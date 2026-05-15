"""Book 测试共享 fixture。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from pypdf import PdfWriter


@pytest.fixture
def make_pdf(tmp_path: Path) -> Callable[..., Path]:
    """在 ``tmp_path`` 下生成简单多页 PDF。"""

    def _make(rel: str, pages: int = 1) -> Path:
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=612, height=792)
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as f:
            writer.write(f)
        return dest

    return _make
