"""文件名安全化（跨平台，保留中文）。"""

from __future__ import annotations

import re
import unicodedata

from paperize.config import MAX_TITLE_FILENAME_LEN

# Windows 保留名（节选）
_WIN_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}

# Windows / 通用非法文件名字符
_ILLEGAL_RE = re.compile(r'[<>:"/\\\\|?*\\x00-\\x1f]')


def safe_filename(title: str, max_len: int = MAX_TITLE_FILENAME_LEN) -> str:
    """将标题转为可用作文件名的字符串，保留中文。"""
    raw = (title or "").strip()
    if not raw:
        return "untitled"

    # 规范化并移除不可见控制字符
    raw = unicodedata.normalize("NFKC", raw)
    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Cc")

    raw = _ILLEGAL_RE.sub("_", raw)
    raw = raw.rstrip(" .")  # Windows 不允许尾随空格或点

    raw = raw.strip()
    if not raw:
        return "untitled"

    stem = raw[:max_len].rstrip(" .")
    if not stem:
        stem = "untitled"

    if stem.lower() in _WIN_RESERVED:
        stem = f"_{stem}_"

    return stem or "untitled"
