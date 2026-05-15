"""paths 与 manifest 路径校验。"""

from pathlib import Path

import pytest

from simpread_paperize.book.manifest import ManifestError, parse_manifest_dict
from simpread_paperize.book.paths import PathEscapeError, resolve_under_manifest_dir


def test_resolve_relative_ok(tmp_path: Path) -> None:
    base = tmp_path.resolve()
    p = resolve_under_manifest_dir(base, "sub/a.pdf")
    assert p == base / "sub" / "a.pdf"


def test_reject_parent(tmp_path: Path) -> None:
    with pytest.raises(PathEscapeError):
        resolve_under_manifest_dir(tmp_path, "../x.pdf")


def test_manifest_escape_in_article(tmp_path: Path) -> None:
    mf = tmp_path / "manifest.yaml"
    mf.write_text("x", encoding="utf-8")
    data = {
        "schema_version": 1,
        "book": {"title": "t", "trace_header": "h"},
        "volumes": [{"cover_pdf": "c.pdf", "articles": [{"title": "x", "path": "../evil.pdf"}]}],
    }
    with pytest.raises(ManifestError):
        parse_manifest_dict(data, mf)


def test_article_path_preserves_leading_space(tmp_path: Path) -> None:
    """文件名若以空白开头，manifest 路径不得 strip，否则 index/构建会找不到文件。"""
    spaced_name = " spaced.pdf"
    (tmp_path / spaced_name).write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    mf = tmp_path / "manifest.yaml"
    mf.write_text("x", encoding="utf-8")
    data = {
        "schema_version": 1,
        "book": {"title": "t", "trace_header": "h"},
        "volumes": [
            {
                "cover_pdf": "c.pdf",
                "articles": [{"title": "x", "path": spaced_name}],
            }
        ],
    }
    (tmp_path / "c.pdf").write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    model = parse_manifest_dict(data, mf)
    assert model.volumes[0].articles[0].path == spaced_name
    resolved = resolve_under_manifest_dir(tmp_path, spaced_name)
    assert resolved.is_file()
