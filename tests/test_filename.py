"""文件名安全化测试。"""

from simpread_paperize.filename import safe_filename


def test_safe_filename_chinese() -> None:
    assert safe_filename("  我的标题  ") == "我的标题"


def test_safe_filename_illegal_windows() -> None:
    s = safe_filename('a<b>c:d"e|f?g*h')
    assert "<" not in s
    assert ":" not in s


def test_empty_title() -> None:
    assert safe_filename("") == "untitled"
    assert safe_filename("   ") == "untitled"


def test_trailing_dot_space() -> None:
    s = safe_filename("hello . ")
    assert not s.endswith(" ")
    assert not s.endswith(".")


def test_reserved_con() -> None:
    s = safe_filename("CON")
    assert s != "CON" or s.startswith("_")
