"""生成 manifest.yaml：支持扫描目录内 PDF 生成初版。"""

from __future__ import annotations

from pathlib import Path

import yaml
from pypdf import PdfWriter

MANIFEST_FILENAME = "manifest.yaml"

PLACEHOLDER_COVER_REL = "covers/_sr_book_placeholder_cover.pdf"

STATIC_TEMPLATE = """schema_version: 1
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


def _write_blank_cover_pdf(dest: Path) -> None:
    """一页空白 A4（占位封面）；若文件已存在则不覆盖。"""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    with dest.open("wb") as f:
        w.write(f)


def collect_pdf_paths_relative(base: Path, *, recursive: bool) -> list[str]:
    """返回相对 ``base`` 的 POSIX 路径，已排序；排除占位封面自身。"""
    base = base.resolve()
    if recursive:
        candidates = [p for p in base.rglob("*.pdf") if p.is_file()]
    else:
        candidates = [p for p in base.glob("*.pdf") if p.is_file()]
    skip = PLACEHOLDER_COVER_REL.replace("\\", "/").lower()
    rels: list[str] = []
    for p in candidates:
        rel = p.resolve().relative_to(base).as_posix()
        if rel.lower() == skip:
            continue
        rels.append(rel)
    rels.sort(key=lambda s: s.lower())
    return rels


def _manifest_yaml_from_scan(base: Path, pdf_rels: list[str]) -> str:
    book_title = base.name or "未命名书目"
    data: dict = {
        "schema_version": 1,
        "book": {
            "title": book_title,
            "trace_header": "请修改为批次或追溯字符串",
        },
        "max_pages_per_volume": 400,
        "toc_pages_per_volume": 1,
        "volumes": [
            {
                "cover_pdf": PLACEHOLDER_COVER_REL,
                "articles": [
                    {"title": Path(rel).stem, "path": rel} for rel in pdf_rels
                ],
            }
        ],
    }
    return yaml.safe_dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)


def write_manifest_template(
    target_dir: Path,
    *,
    force: bool = False,
    scan: bool = True,
    recursive: bool = True,
) -> tuple[Path, int]:
    """
    在 ``target_dir`` 写入 ``manifest.yaml``。

    若 ``scan`` 为真：收集目录下 ``*.pdf``（默认 ``recursive=True`` 含子目录；``recursive=False`` 时仅根目录），
    若有至少一个文件则生成**初版 manifest**（篇名取文件名去扩展名，路径为相对路径），
    并写入一页空白占位封面 ``covers/_sr_book_placeholder_cover.pdf``（已存在则不覆盖）。
    若未找到任何 PDF，则回退为静态教学模板。

    返回 ``(manifest 路径, 扫描到的 PDF 篇数)``；静态模板且无扫描命中时篇数为 ``0``。
    """
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / MANIFEST_FILENAME
    if dest.exists() and not force:
        raise FileExistsError(str(dest))

    scanned_count = 0
    if scan:
        pdf_rels = collect_pdf_paths_relative(target_dir, recursive=recursive)
        scanned_count = len(pdf_rels)
        if pdf_rels:
            cover_abs = target_dir / PLACEHOLDER_COVER_REL
            _write_blank_cover_pdf(cover_abs)
            dest.write_text(_manifest_yaml_from_scan(target_dir, pdf_rels), encoding="utf-8")
        else:
            dest.write_text(STATIC_TEMPLATE, encoding="utf-8")
    else:
        dest.write_text(STATIC_TEMPLATE, encoding="utf-8")
    return dest, scanned_count
