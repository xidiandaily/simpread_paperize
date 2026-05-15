"""build：合并封面、目录、正文，叠页眉脚与篇级书签。"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from simpread_paperize.book.manifest import ManifestModel, load_manifest
from simpread_paperize.book.paths import resolve_under_manifest_dir
from simpread_paperize.book.toc_pdf import render_overlay_page, render_toc_pdf


class BuildError(RuntimeError):
    """合并或写出失败。"""


def load_plan_dict(plan_path: Path) -> dict:
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BuildError("plan.json 根必须为对象。")
    return data


def _append_all_pages(writer: PdfWriter, reader: PdfReader) -> None:
    for page in reader.pages:
        writer.add_page(page)


def build_volume_pdf(
    vol: dict,
    model: ManifestModel,
    *,
    output_path: Path,
    overwrite: bool,
) -> None:
    if output_path.exists() and not overwrite:
        raise BuildError(f"输出已存在（请加 --overwrite）：{output_path}")
    mdir = model.manifest_dir
    writer = PdfWriter()
    writer.page_mode = "/UseOutlines"

    cover_rel = vol["cover_pdf"]
    cover_abs = resolve_under_manifest_dir(mdir, cover_rel)
    if not cover_abs.is_file():
        raise BuildError(f"找不到封面：{cover_rel}")
    with cover_abs.open("rb") as f:
        cover_reader = PdfReader(f)
        _append_all_pages(writer, cover_reader)

    toc_entries = [(a["title"], a["start_page"]) for a in vol.get("articles", [])]
    toc_bytes = render_toc_pdf(toc_entries)
    toc_reader = PdfReader(BytesIO(toc_bytes))
    _append_all_pages(writer, toc_reader)

    article_start_indices: list[int] = []
    for art in vol.get("articles", []):
        article_start_indices.append(len(writer.pages))
        art_abs = resolve_under_manifest_dir(mdir, art["path"])
        if not art_abs.is_file():
            raise BuildError(f"找不到篇目：{art['path']}")
        with art_abs.open("rb") as f:
            ar = PdfReader(f)
            _append_all_pages(writer, ar)

    total_pages = len(writer.pages)
    header = model.trace_header

    for i in range(total_pages):
        page = writer.pages[i]
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        overlay = PdfReader(BytesIO(render_overlay_page(w, h, header, i + 1, total_pages)))
        page.merge_page(overlay.pages[0])

    for idx, art in enumerate(vol.get("articles", [])):
        pg = article_start_indices[idx]
        writer.add_outline_item(title=art["title"], page_number=pg)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        writer.write(f)


def run_build(
    manifest_path: Path,
    plan_path: Path,
    output_dir: Path,
    *,
    overwrite: bool,
    temp_dir: Path | None = None,
) -> list[Path]:
    """``temp_dir`` 预留：当前合并主要在内存完成；若将来写中间文件则优先使用该目录。"""
    _ = temp_dir
    model = load_manifest(manifest_path)
    pdata = load_plan_dict(plan_path)
    if not pdata.get("success", False):
        raise BuildError("plan.json 标记为失败（success=false），请先修复后重新 plan。")
    vols = pdata.get("volumes")
    if not isinstance(vols, list):
        raise BuildError("plan.json 缺少 volumes 数组。")
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for vol in vols:
        if not isinstance(vol, dict):
            continue
        vi = vol.get("volume_index")
        if not isinstance(vi, int):
            continue
        out = output_dir / f"volume-{vi:02d}.pdf"
        build_volume_pdf(vol, model, output_path=out, overwrite=overwrite)
        written.append(out)
    return written
