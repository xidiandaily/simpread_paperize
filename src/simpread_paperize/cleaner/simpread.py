"""简悦（Simpread）离线 HTML 清洗。"""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from simpread_paperize.cleaner.base import BaseCleaner
from simpread_paperize.models import CleanResult

_REMOVE_TAG_NAMES = frozenset(
    {
        "toc",
        "toc-bg",
        "read-process",
        "sr-rd-crlbar",
        "simpread-highlight",
        "sr-snapshot-ctlbar",
        "simpread-feedback",
        "simpread-urlscheme",
        "script",
        "iframe",
    }
)


def _find_first_tag(soup: BeautifulSoup, name: str) -> Tag | None:
    target = name.lower()
    for tag in soup.find_all(True):
        if isinstance(tag, Tag) and tag.name and tag.name.lower() == target:
            return tag
    return None


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _normalize_author_display(text: str) -> str:
    """简悦聚合回答中 sr-rd-mult-avatar 内的昵称（去掉零宽字符与多余空白）。"""
    t = (text or "").replace("\u200b", "").replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "")
    return _normalize_ws(t)


def _owner_document(tag: Tag) -> BeautifulSoup:
    cur: Tag | BeautifulSoup = tag
    while cur.parent is not None:
        cur = cur.parent
    assert isinstance(cur, BeautifulSoup)
    return cur


def _promote_mult_avatars(root: Tag | BeautifulSoup) -> None:
    """将 sr-rd-mult-avatar（头像 + 昵称）替换为可打印的作者行，避免昵称随整块删除。"""
    for av in list(root.find_all("sr-rd-mult-avatar")):
        if not isinstance(av, Tag):
            continue
        label = _normalize_author_display(av.get_text())
        if not label:
            av.decompose()
            continue
        doc = _owner_document(av)
        row = doc.new_tag("div", attrs={"class": "paperize-mult-author"})
        row.string = label
        av.replace_with(row)


class SimpreadCleaner(BaseCleaner):
    """识别并清洗简悦导出 HTML。"""

    def match(self, html: str) -> bool:
        lower = html.lower()
        if "sr-rd-content" in lower or "sr-rd-title" in lower or "sr-read" in lower:
            return True
        if "simpread" in lower:
            return True
        if "简悦" in html or "simpread" in html:
            return True
        return False

    def _extract_title(self, soup: BeautifulSoup, source_path: Path | None) -> str:
        el = _find_first_tag(soup, "sr-rd-title")
        if el and el.get_text(strip=True):
            return _normalize_ws(el.get_text())

        ht = soup.find("title")
        if ht and ht.get_text(strip=True):
            t = _normalize_ws(ht.get_text())
            if t:
                return t

        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return _normalize_ws(h1.get_text())

        if source_path:
            return _normalize_ws(source_path.stem)

        return "Untitled"

    def _extract_body_fragment(self, soup: BeautifulSoup) -> Tag:
        content = _find_first_tag(soup, "sr-rd-content")
        if content:
            inner = content.decode_contents() or ""
            wrapped = BeautifulSoup(f"<div id='paperize-inner'>{inner}</div>", "html.parser")
            node = wrapped.find("div", id="paperize-inner")
            assert node is not None
            return node

        if soup.body:
            return soup.body
        inner_html = str(soup)
        wrapped = BeautifulSoup(f"<div id='paperize-inner'>{inner_html}</div>", "html.parser")
        node = wrapped.find("div", id="paperize-inner")
        assert node is not None
        return node

    def _strip_noise(self, root: Tag | BeautifulSoup) -> list[str]:
        warnings: list[str] = []
        for tag in list(root.find_all(True)):
            if not isinstance(tag, Tag) or not tag.name:
                continue
            n = tag.name.lower()
            if n in _REMOVE_TAG_NAMES:
                tag.decompose()
        return warnings

    def _build_document(self, title: str, article_inner: str) -> str:
        esc_title = html_lib.escape(title or "")
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{esc_title}</title>
</head>
<body>
  <main class="paperize-document paperize-simpread">
    <h1 class="paperize-title">{esc_title}</h1>
    <article class="paperize-content">
{article_inner}
    </article>
  </main>
</body>
</html>
"""

    def clean(self, html: str, source_path: Path | None = None) -> CleanResult:
        warnings: list[str] = []
        soup = BeautifulSoup(html, "lxml")
        title = self._extract_title(soup, source_path)

        fragment_root = self._extract_body_fragment(soup)
        if isinstance(fragment_root, BeautifulSoup) and fragment_root.body:
            work = fragment_root.body
        elif isinstance(fragment_root, Tag):
            work = fragment_root
        else:
            work = soup.body or soup

        _promote_mult_avatars(work)
        self._strip_noise(work)
        inner_html = "".join(str(c) for c in work.children if not isinstance(c, NavigableString) or str(c).strip())

        # 若正文几乎为空，记录警告
        text_preview = BeautifulSoup(inner_html, "lxml").get_text(strip=True)[:200]
        if not text_preview:
            warnings.append("正文区域可能为空，请检查源文件或 sr-rd-content。")

        out_html = self._build_document(title, inner_html.strip())
        return CleanResult(title=title, html=out_html, source_type="simpread", warnings=warnings)
