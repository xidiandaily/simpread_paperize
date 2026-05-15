"""index：数字前缀重命名与 manifest 回写。"""

from __future__ import annotations

import re
from pathlib import Path

from simpread_paperize.book.manifest import ManifestModel, save_manifest
from simpread_paperize.book.paths import resolve_under_manifest_dir


class IndexRenameError(RuntimeError):
    """重命名冲突或非法路径。"""


_NUM_PREFIX = re.compile(r"^\d+_")


def strip_leading_index_prefix(filename: str) -> str:
    return _NUM_PREFIX.sub("", filename, count=1)


def plan_renames(model: ManifestModel) -> list[tuple[str, str]]:
    """
    返回 (旧相对路径, 新相对路径) 列表，顺序与全局篇序一致。
    """
    mdir = model.manifest_dir
    ops: list[tuple[str, str]] = []
    idx = 0
    for vol in model.volumes:
        for art in vol.articles:
            idx += 1
            old_rel = art.path
            abs_old = resolve_under_manifest_dir(mdir, old_rel)
            if abs_old.suffix.lower() != ".pdf":
                raise IndexRenameError(f"非 PDF 篇目：{old_rel}")
            parent = abs_old.parent
            new_base = f"{idx}_{strip_leading_index_prefix(abs_old.name)}"
            abs_new = parent / new_base
            new_rel = abs_new.relative_to(mdir.resolve()).as_posix()
            if old_rel != new_rel:
                ops.append((old_rel, new_rel))
    return ops


def _rename_two_phase(mdir: Path, pairs: list[tuple[Path, Path]]) -> None:
    """避免环换名：先迁至临时名再迁至目标。"""
    tmp_suffix = ".__srbook_tmp__"
    phase1: list[tuple[Path, Path]] = []
    for old_abs, new_abs in pairs:
        if old_abs == new_abs:
            continue
        tmp = old_abs.with_name(old_abs.name + tmp_suffix)
        if tmp.exists():
            raise IndexRenameError(f"临时文件已存在：{tmp}")
        phase1.append((old_abs, tmp))
    for old_abs, tmp in phase1:
        old_abs.rename(tmp)
    phase2: list[tuple[Path, Path]] = []
    for old_abs, new_abs in pairs:
        if old_abs == new_abs:
            continue
        tmp = old_abs.with_name(old_abs.name + tmp_suffix)
        phase2.append((tmp, new_abs))
    for tmp, new_abs in phase2:
        if new_abs.exists():
            raise IndexRenameError(f"目标已存在：{new_abs}")
        tmp.rename(new_abs)


def apply_renames(model: ManifestModel, dry_run: bool) -> list[tuple[str, str]]:
    """
    执行重命名并回写 manifest（``dry_run`` 时不写磁盘、不改 YAML）。
    返回已执行（或拟执行）的 (旧, 新) 相对路径对。
    """
    mdir = model.manifest_dir.resolve()
    ops_rel = plan_renames(model)
    abs_pairs: list[tuple[Path, Path]] = []
    for old_r, new_r in ops_rel:
        old_abs = resolve_under_manifest_dir(mdir, old_r)
        new_abs = resolve_under_manifest_dir(mdir, new_r)
        if not old_abs.is_file():
            raise IndexRenameError(f"源文件不存在：{old_r}")
        if new_abs != old_abs and new_abs.exists():
            raise IndexRenameError(f"目标已存在：{new_r}")
        abs_pairs.append((old_abs, new_abs))
    if dry_run:
        return ops_rel
    if not abs_pairs:
        return ops_rel
    _rename_two_phase(mdir, abs_pairs)
    rel_map = {o: n for o, n in ops_rel}
    for vol in model.volumes:
        for art in vol.articles:
            if art.path in rel_map:
                art.path = rel_map[art.path]
    save_manifest(model)
    return ops_rel
