"""Simpread Paperize 命令行入口。"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from simpread_paperize.convert import collect_html_files, convert_batch, convert_one
from simpread_paperize.models import ConvertOptions

console = Console(stderr=False)
err_console = Console(stderr=True)


def _main(
    input_path: Annotated[Path, typer.Argument(help="输入 HTML 文件或包含 .html/.htm 的目录")],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="单文件模式：输出 PDF 路径"),
    ] = None,
    out_dir: Annotated[
        Optional[Path],
        typer.Option("--out", help="目录模式：输出 PDF 所在目录"),
    ] = None,
    recursive: Annotated[bool, typer.Option("--recursive", "-r", help="递归扫描子目录")] = False,
    paper: Annotated[str, typer.Option("--paper", help="纸张，默认 A4")] = "A4",
    margin: Annotated[str, typer.Option("--margin", help="页边距，如 14mm")] = "14mm",
    debug: Annotated[bool, typer.Option("--debug", help="保存 original/cleaned/CSS/render.log")] = False,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="允许覆盖已存在 PDF")] = False,
    traceback_debug: Annotated[
        bool,
        typer.Option("--traceback", help="失败时打印 Python 堆栈"),
    ] = False,
) -> None:
    """
    Simpread Paperize：将简悦（Simpread）等离线 HTML 转为 A4 打印友好 PDF。

    单文件：sr_paperize 文章.html -o 输出.pdf

    批量：sr_paperize ./备份目录 --out ./pdf --recursive
    """
    try:
        if input_path.is_dir():
            if out_dir is None:
                err_console.print("[red]错误：[/red]输入为目录时必须指定 --out 输出目录。")
                raise typer.Exit(code=1)
            opts = ConvertOptions(
                input_path=input_path,
                output_pdf=None,
                output_dir=out_dir,
                recursive=recursive,
                paper=paper,
                margin=margin,
                debug=debug,
                overwrite=overwrite,
            )
            files = collect_html_files(input_path, recursive)
            if not files:
                err_console.print("[yellow]提示：[/yellow]未找到任何 .html / .htm 文件。")
                raise typer.Exit(code=1)
            console.print(f"[cyan]共发现 {len(files)} 个 HTML 文件，开始转换…[/cyan]")
            results = convert_batch(input_path, out_dir, opts)
            ok = sum(1 for r in results if r.success)
            bad = len(results) - ok
            console.print(
                f"[green]成功：[/green]{ok}　[red]失败：[/red]{bad}　[blue]输出目录：[/blue]{out_dir.resolve()}"
            )
            for r in results:
                if not r.success:
                    err_console.print(f"[red]✗[/red] {r.input_path} — {r.message}")
                elif debug and r.debug_dir:
                    console.print(f"[dim]调试：[/dim]{r.debug_dir}")
            raise typer.Exit(code=1 if bad else 0)

        if not input_path.is_file():
            err_console.print("[red]错误：[/red]输入路径不是文件或目录。")
            raise typer.Exit(code=1)

        if out_dir is not None:
            err_console.print("[red]错误：[/red]单文件模式下请使用 -o / --output，不要使用 --out。")
            raise typer.Exit(code=1)

        out_pdf = output if output is not None else input_path.with_suffix(".pdf")
        opts = ConvertOptions(
            input_path=input_path,
            output_pdf=out_pdf,
            output_dir=None,
            recursive=False,
            paper=paper,
            margin=margin,
            debug=debug,
            overwrite=overwrite,
        )
        console.print("[cyan]正在转换…[/cyan]")
        res = convert_one(input_path, out_pdf, opts)
        if res.success:
            console.print(f"[green]{res.message}[/green]")
            if debug and res.debug_dir:
                console.print(f"[blue]调试目录：[/blue]{res.debug_dir.resolve()}")
            raise typer.Exit(code=0)
        err_console.print(f"[red]{res.message}[/red]")
        if traceback_debug:
            traceback.print_exc()
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        err_console.print(f"[red]未处理的错误：[/red]{e}")
        if traceback_debug:
            traceback.print_exc()
        raise typer.Exit(code=1) from e


def app() -> None:
    """控制台入口 `sr_paperize = simpread_paperize.cli:app`。"""
    typer.run(_main)


if __name__ == "__main__":
    app()
