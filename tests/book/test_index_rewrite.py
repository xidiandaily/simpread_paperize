"""index 重命名与 manifest 回写。"""

from pathlib import Path

import yaml

from simpread_paperize.book.index_rename import apply_renames
from simpread_paperize.book.manifest import load_manifest


def _write_manifest(tmp_path: Path, paths: tuple[str, str, str]) -> Path:
    c, a, b = paths
    data = {
        "schema_version": 1,
        "book": {"title": "t", "trace_header": "h"},
        "max_pages_per_volume": 400,
        "toc_pages_per_volume": 1,
        "volumes": [
            {
                "cover_pdf": c,
                "articles": [
                    {"title": "A", "path": a},
                    {"title": "B", "path": b},
                ],
            }
        ],
    }
    mf = tmp_path / "manifest.yaml"
    mf.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return mf


def test_index_dry_run_no_filesystem_change(tmp_path: Path, make_pdf) -> None:
    make_pdf("covers/c1.pdf")
    a = make_pdf("articles/a.pdf")
    b = make_pdf("articles/b.pdf")
    mf = _write_manifest(tmp_path, ("covers/c1.pdf", "articles/a.pdf", "articles/b.pdf"))
    text_before = mf.read_text(encoding="utf-8")
    model = load_manifest(mf)
    ops = apply_renames(model, dry_run=True)
    assert len(ops) == 2
    assert mf.read_text(encoding="utf-8") == text_before
    assert a.name == "a.pdf"


def test_index_renames_and_updates_manifest(tmp_path: Path, make_pdf) -> None:
    make_pdf("covers/c1.pdf")
    make_pdf("articles/a.pdf")
    make_pdf("articles/b.pdf")
    mf = _write_manifest(tmp_path, ("covers/c1.pdf", "articles/a.pdf", "articles/b.pdf"))
    model = load_manifest(mf)
    apply_renames(model, dry_run=False)
    model2 = load_manifest(mf)
    paths = [a.path for v in model2.volumes for a in v.articles]
    assert paths == ["articles/1_a.pdf", "articles/2_b.pdf"]
    assert (tmp_path / "articles" / "1_a.pdf").is_file()
