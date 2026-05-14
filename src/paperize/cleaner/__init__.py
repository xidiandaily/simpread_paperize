"""Cleaner 注册与导出。"""

from __future__ import annotations

from paperize.cleaner.base import BaseCleaner
from paperize.cleaner.generic import GenericCleaner
from paperize.cleaner.simpread import SimpreadCleaner

def choose_cleaner(html: str) -> BaseCleaner:
    """按优先级选择适用的清洗器实例。"""
    simp = SimpreadCleaner()
    if simp.match(html):
        return simp
    return GenericCleaner()
