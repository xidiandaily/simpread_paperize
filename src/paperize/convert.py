"""单文件 / 批量转换编排。"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from paperize.cleaner import choose_cleaner
from paperize.config import styles_dir
from paperize.filename import safe_filename
from paperize.models import CleanResult, ConvertOptions, ConvertResult
from paperize.renderer import render_pdf


def _css_paths_for(clean: CleanResult) -> list[Path]:
    base = styles_dir()
    paths = [base / "paperize-base.css"]
    if clean.source_type == "simpread":
        paths.append(base / "simpread-a4.css")
    else:
        paths.append(base / "generic-a4.css")
    return paths


def _unique_debug_dir(slug: Path) -> Path:
    root = Path.cwd() / ".paperize-debug"
    candidate = root / slug
    if not candidate.exists():
        return candidate
    for i in range(2, 1000):
        alt = root / f"{slug}_{i}"
        if not alt.exists():
            return alt
    return root / f"{slug}_many"


def _write_debug_bundle(
    debug_dir: Path,
    original_html: str,
    cleaned_html: str,
    css_paths: list[Path],
    log_text: str,
) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / "original.html").write_text(original_html, encoding="utf-8")
    (debug_dir / "cleaned.html").write_text(cleaned_html, encoding="utf-8")
    for p in css_paths:
        if p.is_file():
            shutil.copy2(p, debug_dir / p.name)
    (debug_dir / "render.log").write_text(log_text, encoding="utf-8")


def convert_one(input_path: Path, output_pdf: Path, options: ConvertOptions) -> ConvertResult:
    """读取 HTML → 清洗 → 渲染 PDF。"""
    log_lines: list[str] = []
    debug_dir: Path | None = None

    try:
        if not input_path.is_file():
            return ConvertResult(
                input_path=input_path,
                output_path=None,
                success=False,
                message="输入不是有效的文件路径。",
            )

        raw = input_path.read_text(encoding="utf-8", errors="replace")
        log_lines.append("已读取源 HTML。")

        cleaner = choose_cleaner(raw)
        clean: CleanResult = cleaner.clean(raw, source_path=input_path)
        log_lines.append(f"已清洗（来源类型: {clean.source_type}）。")

        if options.debug:
            debug_dir = _unique_debug_dir(Path(safe_filename(clean.title)))
            log_lines.append(f"调试目录: {debug_dir}")

        css_paths = _css_paths_for(clean)

        with tempfile.TemporaryDirectory(prefix="paperize-") as tmp:
            cleaned_path = Path(tmp) / "cleaned.html"
            cleaned_path.write_text(clean.html, encoding="utf-8")

            if options.debug and debug_dir is not None:
                _write_debug_bundle(debug_dir, raw, clean.html, css_paths, "\n".join(log_lines))

            if output_pdf.exists() and not options.overwrite:
                msg = f"目标 PDF 已存在: {output_pdf}。请使用 --overwrite 覆盖。"
                log_lines.append(msg)
                if options.debug and debug_dir is not None:
                    (debug_dir / "render.log").write_text("\n".join(log_lines), encoding="utf-8")
                return ConvertResult(
                    input_path=input_path,
                    output_path=None,
                    success=False,
                    message=msg,
                    debug_dir=debug_dir,
                )

            render_pdf(cleaned_path, output_pdf, options, css_paths, log_lines=log_lines)

        if options.debug and debug_dir is not None:
            (debug_dir / "render.log").write_text("\n".join(log_lines), encoding="utf-8")

        return ConvertResult(
            input_path=input_path,
            output_path=output_pdf,
            success=True,
            message=f"已生成 PDF：{output_pdf}",
            debug_dir=debug_dir,
        )
    except FileNotFoundError as e:
        msg = f"文件未找到: {e}"
        log_lines.append(msg)
        if options.debug and debug_dir is not None:
            (debug_dir / "render.log").write_text("\n".join(log_lines), encoding="utf-8")
        return ConvertResult(input_path=input_path, output_path=None, success=False, message=msg, debug_dir=debug_dir)
    except Exception as e:
        err = f"转换失败: {type(e).__name__}: {e}"
        log_lines.append(err)
        hint = "若提示缺少浏览器，请运行：uv run playwright install chromium"
        log_lines.append(hint)
        if options.debug and debug_dir is not None:
            (debug_dir / "render.log").write_text("\n".join(log_lines), encoding="utf-8")
        return ConvertResult(
            input_path=input_path,
            output_path=None,
            success=False,
            message=f"{err}。{hint}",
            debug_dir=debug_dir,
        )


def collect_html_files(directory: Path, recursive: bool) -> list[Path]:
    """收集目录下 .html / .htm 文件。"""
    patterns = ("*.html", "*.htm")
    found: list[Path] = []
    if recursive:
        for pat in patterns:
            found.extend(sorted(directory.rglob(pat)))
    else:
        for pat in patterns:
            found.extend(sorted(directory.glob(pat)))
    # 去重保持顺序
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def convert_batch(
    input_dir: Path,
    output_dir: Path,
    options: ConvertOptions,
) -> list[ConvertResult]:
    """批量转换目录内 HTML，每个文件独立 try/except 语义在 CLI 层处理亦可。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = collect_html_files(input_dir, options.recursive)
    results: list[ConvertResult] = []
    for fp in files:
        raw = fp.read_text(encoding="utf-8", errors="replace")
        cleaner = choose_cleaner(raw)
        pre = cleaner.clean(raw, source_path=fp)
        base_name = safe_filename(pre.title)
        out_path = output_dir / f"{base_name}.pdf"
        if out_path.exists() and not options.overwrite:
            stem = base_name
            chosen = False
            for i in range(2, 10_000):
                cand = output_dir / f"{stem}_{i}.pdf"
                if not cand.exists():
                    out_path = cand
                    chosen = True
                    break
            if not chosen:
                results.append(
                    ConvertResult(
                        input_path=fp,
                        output_path=None,
                        success=False,
                        message="输出文件名冲突，请使用 --overwrite 或清理输出目录。",
                        debug_dir=None,
                    )
                )
                continue
        results.append(convert_one(fp, out_path, options))
    return results
