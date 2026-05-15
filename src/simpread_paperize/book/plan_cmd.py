"""plan：页数统计、表格输出、plan.json。"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader
from rich.console import Console
from rich.table import Table

from simpread_paperize.book.manifest import ManifestError, ManifestModel, load_manifest
from simpread_paperize.book.paths import PathEscapeError, resolve_under_manifest_dir
from simpread_paperize.book.volume_plan import BookPlan, PlanErrorEntry, compute_book_plan


def count_pdf_pages(path: Path) -> int:
    with path.open("rb") as f:
        reader = PdfReader(f)
        return len(reader.pages)


def build_plan_from_manifest(model: ManifestModel) -> BookPlan:
    mdir = model.manifest_dir
    article_pages: dict[str, int] = {}
    for art in model.global_articles():
        try:
            p = resolve_under_manifest_dir(mdir, art.path)
        except PathEscapeError as exc:
            return BookPlan(
                manifest_path=str(model.manifest_path),
                max_pages_per_volume=model.max_pages_per_volume,
                toc_pages_per_volume=model.toc_pages_per_volume,
                success=False,
                errors=[PlanErrorEntry("PATH_ESCAPE", str(exc), art.path)],
            )
        if not p.is_file():
            return BookPlan(
                manifest_path=str(model.manifest_path),
                max_pages_per_volume=model.max_pages_per_volume,
                toc_pages_per_volume=model.toc_pages_per_volume,
                success=False,
                errors=[PlanErrorEntry("FILE_NOT_FOUND", f"找不到篇目 PDF：{art.path}", art.path)],
            )
        try:
            article_pages[art.path] = count_pdf_pages(p)
        except Exception as exc:  # noqa: BLE001
            return BookPlan(
                manifest_path=str(model.manifest_path),
                max_pages_per_volume=model.max_pages_per_volume,
                toc_pages_per_volume=model.toc_pages_per_volume,
                success=False,
                errors=[PlanErrorEntry("NOT_PDF", f"无法读取 PDF：{exc}", art.path)],
            )

    volume_cover_pages: list[int] = []
    for vol in model.volumes:
        try:
            cp = resolve_under_manifest_dir(mdir, vol.cover_pdf)
        except PathEscapeError as exc:
            return BookPlan(
                manifest_path=str(model.manifest_path),
                max_pages_per_volume=model.max_pages_per_volume,
                toc_pages_per_volume=model.toc_pages_per_volume,
                success=False,
                errors=[PlanErrorEntry("PATH_ESCAPE", str(exc), vol.cover_pdf)],
            )
        if not cp.is_file():
            return BookPlan(
                manifest_path=str(model.manifest_path),
                max_pages_per_volume=model.max_pages_per_volume,
                toc_pages_per_volume=model.toc_pages_per_volume,
                success=False,
                errors=[PlanErrorEntry("FILE_NOT_FOUND", f"找不到封面：{vol.cover_pdf}", vol.cover_pdf)],
            )
        try:
            volume_cover_pages.append(count_pdf_pages(cp))
        except Exception as exc:  # noqa: BLE001
            return BookPlan(
                manifest_path=str(model.manifest_path),
                max_pages_per_volume=model.max_pages_per_volume,
                toc_pages_per_volume=model.toc_pages_per_volume,
                success=False,
                errors=[PlanErrorEntry("NOT_PDF", f"无法读取封面 PDF：{exc}", vol.cover_pdf)],
            )

    return compute_book_plan(model, article_pages, volume_cover_pages)


def render_plan_table(plan: BookPlan) -> Table:
    table = Table(title="成书规划", show_header=True, header_style="bold")
    table.add_column("卷", justify="right")
    table.add_column("篇名")
    table.add_column("篇页数", justify="right")
    table.add_column("起始页", justify="right")
    table.add_column("卷总页", justify="right")
    for v in plan.volumes:
        first = True
        for a in v.articles:
            table.add_row(
                str(v.volume_index) if first else "",
                a.title,
                str(a.pages),
                str(a.start_page),
                str(v.total_pages) if first else "",
            )
            first = False
        if not v.articles:
            table.add_row(str(v.volume_index), "(无篇目)", "-", "-", str(v.total_pages))
    return table


def write_plan_json(path: Path, plan: BookPlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.to_json_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def run_plan_cli(
    manifest_path: Path,
    plan_out: Path | None,
    quiet: bool,
    console: Console,
    err_console: Console,
) -> BookPlan:
    try:
        model = load_manifest(manifest_path)
    except ManifestError as exc:
        plan = BookPlan(
            manifest_path=str(manifest_path.resolve()),
            max_pages_per_volume=400,
            toc_pages_per_volume=1,
            success=False,
            errors=[PlanErrorEntry("MANIFEST_SCHEMA", str(exc), None)],
        )
        err_console.print(f"[red]错误：[/red]{exc}")
        out = plan_out or (manifest_path.parent / "plan.json")
        try:
            write_plan_json(out, plan)
        except OSError as wexc:
            err_console.print(f"[red]无法写入 plan.json：[/red]{wexc}")
        return plan

    plan = build_plan_from_manifest(model)
    out = plan_out or (model.manifest_dir / "plan.json")
    try:
        write_plan_json(out, plan)
    except OSError as exc:
        err_console.print(f"[red]无法写入 plan.json：[/red]{exc}")
        fail = BookPlan(
            manifest_path=str(model.manifest_path),
            max_pages_per_volume=model.max_pages_per_volume,
            toc_pages_per_volume=model.toc_pages_per_volume,
            success=False,
            errors=plan.errors
            + [PlanErrorEntry("PLAN_IO", str(exc), str(out))],
        )
        write_plan_json(out, fail)
        return fail

    if not plan.success:
        for e in plan.errors:
            err_console.print(f"[red]{e.code}[/red] {e.message}")
    elif not quiet:
        console.print(render_plan_table(plan))
        console.print(f"\n已写入 [cyan]{out}[/cyan]")
    return plan
