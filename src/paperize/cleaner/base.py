"""Cleaner 抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from paperize.models import CleanResult


class BaseCleaner(ABC):
    """HTML 清洗器基类。"""

    @abstractmethod
    def match(self, html: str) -> bool:
        """判断本清洗器是否适用于该 HTML 字符串。"""

    @abstractmethod
    def clean(self, html: str, source_path: Path | None = None) -> CleanResult:
        """返回标准化后的 HTML 文档字符串。"""
