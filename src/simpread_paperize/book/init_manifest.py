"""生成 manifest.yaml 模板。"""

from __future__ import annotations

from pathlib import Path

MANIFEST_FILENAME = "manifest.yaml"

TEMPLATE = """schema_version: 1
book:
  title: 示例书名
  trace_header: lawrencechi_bookcase_20260514
max_pages_per_volume: 400
toc_pages_per_volume: 1
volumes:
  - cover_pdf: covers/volume1.pdf
    articles:
      - title: 第一篇
        path: articles/article01.pdf
      - title: 第二篇
        path: articles/article02.pdf
  - cover_pdf: covers/volume2.pdf
    articles: []
"""


def write_manifest_template(target_dir: Path, *, force: bool = False) -> Path:
    """在 ``target_dir`` 写入模板；若文件已存在且 ``force`` 为假则抛出 ``FileExistsError``。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / MANIFEST_FILENAME
    if dest.exists() and not force:
        raise FileExistsError(str(dest))
    dest.write_text(TEMPLATE, encoding="utf-8")
    return dest
