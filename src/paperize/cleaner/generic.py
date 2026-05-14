"""非简悦 HTML 的通用清洗。"""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from paperize.cleaner.base import BaseCleaner
from paperize.models import CleanResult


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


class GenericCleaner(BaseCleaner):
    """尽力而为的通用离线页清洗。"""

    def match(self, html: str) -> bool:
        return True

    def _title(self, soup: BeautifulSoup, source_path: Path | None) -> str:
        ht = soup.find("title")
        if ht and ht.get_text(strip=True):
            return _normalize_ws(ht.get_text())
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return _normalize_ws(h1.get_text())
        if source_path:
            return _normalize_ws(source_path.stem)
        return "Untitled"

    def clean(self, html: str, source_path: Path | None = None) -> CleanResult:
        soup = BeautifulSoup(html, "lxml")
        title = self._title(soup, source_path)

        body = soup.body
        if not body:
            inner = str(soup)
        else:
            for tag in list(body.find_all(["script", "iframe"])):
                tag.decompose()
            inner = "".join(
                str(c) for c in body.children if not isinstance(c, NavigableString) or str(c).strip()
            )

        esc = html_lib.escape(title or "")
        out = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{esc}</title>
</head>
<body>
  <main class="paperize-document paperize-generic">
    <h1 class="paperize-title">{esc}</h1>
    <article class="paperize-content">
{inner.strip()}
    </article>
  </main>
</body>
</html>
"""
        return CleanResult(title=title, html=out, source_type="generic", warnings=[])
