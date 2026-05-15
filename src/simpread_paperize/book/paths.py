"""Manifest 目录下的相对路径解析与越界校验。"""

from __future__ import annotations

from pathlib import Path


class PathEscapeError(ValueError):
    """相对路径包含 `..` 或解析后逃出 manifest 目录。"""


def resolve_under_manifest_dir(manifest_dir: Path, relative: str) -> Path:
    """
    将 manifest 内相对路径解析为绝对路径。

    - 禁止绝对路径（POSIX / Windows 盘符）。
    - 禁止含 `..` 的片段。
    - 解析结果必须在 ``manifest_dir.resolve()`` 之下。
    """
    if not relative or not isinstance(relative, str):
        raise PathEscapeError("路径不能为空。")
    rel_path = Path(relative)
    if rel_path.is_absolute():
        raise PathEscapeError("不允许使用绝对路径。")
    if ".." in rel_path.parts:
        raise PathEscapeError("路径中不允许使用 '..'。")
    base = manifest_dir.resolve()
    resolved = (base / rel_path).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise PathEscapeError("路径解析后越出 manifest 所在目录。") from exc
    return resolved
