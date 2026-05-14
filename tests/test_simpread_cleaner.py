"""SimpreadCleaner / Registry 测试。"""

from pathlib import Path

from paperize.cleaner import choose_cleaner
from paperize.cleaner.generic import GenericCleaner
from paperize.cleaner.simpread import SimpreadCleaner

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "simpread_min.html"


def test_simpread_match() -> None:
    c = SimpreadCleaner()
    raw = FIXTURE.read_text(encoding="utf-8")
    assert c.match(raw) is True
    assert c.match("<html><body><p>hi</p></body></html>") is False


def test_choose_cleaner() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    assert isinstance(choose_cleaner(raw), SimpreadCleaner)
    plain = "<!doctype html><html><head><title>x</title></head><body><p>a</p></body></html>"
    assert isinstance(choose_cleaner(plain), GenericCleaner)


def test_simpread_clean_removes_noise() -> None:
    c = SimpreadCleaner()
    raw = FIXTURE.read_text(encoding="utf-8")
    out = c.clean(raw, source_path=FIXTURE).html
    assert "<toc" not in out.lower()
    assert "sr-rd-mult-avatar" not in out
    assert "<script" not in out
    assert "正文保留" in out
    assert "paperize-title" in out
    assert "中文标题示例" in out
    assert "paperize-mult-author" in out
    assert "花朝" in out
    assert "好好组织语言哦" in out
    assert "第一篇回答" in out
    assert "第二篇回答" in out


def test_generic_cleaner() -> None:
    g = GenericCleaner()
    html = "<!doctype html><html><head><title>T</title></head><body><p>x</p><script>1</script></body></html>"
    r = g.clean(html)
    assert r.source_type == "generic"
    assert "<script" not in r.html
    assert "x" in r.html
