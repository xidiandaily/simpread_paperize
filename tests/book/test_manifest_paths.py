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
