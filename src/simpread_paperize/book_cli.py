"""SR Book CLI（`sr_book`）：init / index / plan / build。"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from simpread_paperize.book.index_rename import IndexRenameError, apply_renames, plan_renames
from simpread_paperize.book.init_manifest import PLACEHOLDER_COVER_REL, write_manifest_template
from simpread_paperize.book.manifest import ManifestError, load_manifest
from simpread_paperize.book.merge_build import BuildError, run_build
from simpread_paperize.book.plan_cmd import run_plan_cli

app = typer.Typer(
    help="SR Book：依据 manifest 将多篇 PDF 编排为多卷合集（离线、不修改源单篇 PDF）。",
    no_args_is_help=True,
)
console = Console(stderr=False)
err_console = Console(stderr=True)

_state: dict[str, bool] = {"tb": False}


@app.callback()
def _main_callback(
    traceback_debug: Annotated[
        bool,
        typer.Option("--traceback", help="失败时打印 Python 堆栈"),
    ] = False,
) -> None:
    _state["tb"] = traceback_debug


def _tb() -> bool:
    return bool(_state.get("tb"))


def _exit_code_for_plan(plan) -> int:
    if plan.success:
        return 0
    code = plan.errors[0].code if plan.errors else ""
    if code in ("MANIFEST_PARSE", "MANIFEST_SCHEMA", "PATH_ESCAPE"):
        return 1
    return 2


@app.command()
def init(
    target_dir: Annotated[Path, typer.Argument(help="目标目录（将写入 manifest.yaml）")],
    force: Annotated[bool, typer.Option("--force", help="manifest 已存在时允许覆盖")] = False,
    no_scan: Annotated[
        bool,
        typer.Option(
            "--no-scan",
            help="不扫描 PDF：始终写入固定教学模板（与早期行为一致）",
        ),
    ] = False,
    shallow: Annotated[
        bool,
        typer.Option(
            "--shallow",
            help="仅扫描目标目录根下的 *.pdf，不含子文件夹（默认会递归子目录）",
        ),
    ] = False,
) -> None:
    """生成 manifest：默认递归扫描目录内 PDF 生成初版；无 PDF 时写入静态模板。"""
    try:
        dest, n = write_manifest_template(
            target_dir.resolve(),
            force=force,
            scan=not no_scan,
            recursive=not shallow,
        )
        console.print(f"已生成 [cyan]{dest}[/cyan]")
        if not no_scan and n > 0:
            console.print(
                f"已从目录扫描到 [bold]{n}[/bold] 个 PDF 并写入篇目；"
                f"占位封面为 [cyan]{PLACEHOLDER_COVER_REL}[/cyan]（可替换为你的封面 PDF）。"
            )
        elif not no_scan and n == 0:
            console.print(
                "[dim]目录内未发现 PDF，已写入静态教学模板；放入 PDF 后可执行 "
                "init --force 重新生成初版。[/dim]"
            )
    except FileExistsError:
        err_console.print(
            "[red]错误：[/red]目标目录已存在 manifest.yaml。若需覆盖请加 [bold]--force[/bold]。"
        )
        raise typer.Exit(code=1) from None
    except OSError as exc:
        err_console.print(f"[red]错误：[/red]{exc}")
        if _tb():
            traceback.print_exc()
        raise typer.Exit(code=2) from exc


@app.command("index")
def index_cmd(
    manifest: Annotated[
        Path,
        typer.Option("--manifest", "-m", help="manifest.yaml 路径", exists=True, path_type=Path),
    ],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="仅打印重命名映射，不写磁盘")] = False,
) -> None:
    """按全局篇序添加数字前缀并重写 manifest 路径。"""
    try:
        model = load_manifest(manifest.resolve())
    except ManifestError as exc:
        err_console.print(f"[red]错误：[/red]{exc}")
        raise typer.Exit(code=1) from exc
    try:
        ops = plan_renames(model)
        if dry_run:
            for old, new in ops:
                console.print(f"{old}  ->  {new}")
            if not ops:
                console.print("(无重命名)")
            return
        done = apply_renames(model, dry_run=False)
        for old, new in done:
            console.print(f"[green]已重命名[/green] {old} -> {new}")
        if not done:
            console.print("篇目路径已符合编号，无需更改。")
    except IndexRenameError as exc:
        err_console.print(f"[red]错误：[/red]{exc}")
        if _tb():
            traceback.print_exc()
        raise typer.Exit(code=2) from exc


@app.command()
def plan(
    manifest: Annotated[
        Path,
        typer.Option("--manifest", "-m", help="manifest.yaml 路径", exists=True, path_type=Path),
    ],
    plan_out: Annotated[
        Optional[Path],
        typer.Option("--plan-out", help="plan.json 输出路径（默认同 manifest 目录）"),
    ] = None,
    quiet: Annotated[bool, typer.Option("--quiet", help="不打印人类表格")] = False,
) -> None:
    """分页规划：表格 + plan.json（不写合集 PDF）。"""
    plan_obj = run_plan_cli(manifest.resolve(), plan_out, quiet, console, err_console)
    if not plan_obj.success:
        raise typer.Exit(code=_exit_code_for_plan(plan_obj))


@app.command()
def build(
    manifest: Annotated[
        Path,
        typer.Option("--manifest", "-m", help="manifest.yaml 路径", exists=True, path_type=Path),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="各卷合集 PDF 输出目录", path_type=Path),
    ],
    plan_file: Annotated[
        Optional[Path],
        typer.Option("--plan", help="plan.json（默认同 manifest 目录）", path_type=Path),
    ] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="允许覆盖已存在输出 PDF")] = False,
    temp_dir: Annotated[
        Optional[Path],
        typer.Option("--temp-dir", help="中间文件目录（预留；当前主要在内存合并）", path_type=Path),
    ] = None,
) -> None:
    """依据 manifest 与 plan.json 生成各卷合集 PDF。"""
    m = manifest.resolve()
    p = plan_file if plan_file is not None else m.parent / "plan.json"
    if not p.is_file():
        err_console.print(f"[red]错误：[/red]找不到 plan 文件：{p}")
        raise typer.Exit(code=1)
    try:
        outs = run_build(m, p.resolve(), output_dir.resolve(), overwrite=overwrite, temp_dir=temp_dir)
        for o in outs:
            console.print(f"已写入 [cyan]{o}[/cyan]")
    except ManifestError as exc:
        err_console.print(f"[red]错误：[/red]{exc}")
        raise typer.Exit(code=1) from exc
    except BuildError as exc:
        err_console.print(f"[red]错误：[/red]{exc}")
        if _tb():
            traceback.print_exc()
        raise typer.Exit(code=2) from exc
    except OSError as exc:
        err_console.print(f"[red]错误：[/red]{exc}")
        if _tb():
            traceback.print_exc()
        raise typer.Exit(code=2) from exc
