"""init 子命令。"""

from pathlib import Path

import pytest
import yaml
from pypdf import PdfWriter

from simpread_paperize.book.init_manifest import MANIFEST_FILENAME, write_manifest_template


def _write_one_page_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    with path.open("wb") as f:
        w.write(f)


def test_init_empty_dir_uses_static_template(tmp_path: Path) -> None:
    dest, n = write_manifest_template(tmp_path)
    mf = tmp_path / MANIFEST_FILENAME
    assert mf.is_file()
    assert dest == mf
    data = yaml.safe_load(mf.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert "book" in data and "volumes" in data
    assert n == 0
    assert data["book"]["title"] == "示例书名"


def test_init_refuse_overwrite(tmp_path: Path) -> None:
    write_manifest_template(tmp_path)
    with pytest.raises(FileExistsError):
        write_manifest_template(tmp_path, force=False)


def test_init_force(tmp_path: Path) -> None:
    write_manifest_template(tmp_path)
    write_manifest_template(tmp_path, force=True)
    assert (tmp_path / MANIFEST_FILENAME).is_file()


def test_init_scan_lists_pdfs_in_root(tmp_path: Path) -> None:
    _write_one_page_pdf(tmp_path / "b.pdf")
    _write_one_page_pdf(tmp_path / "a.pdf")
    _, n = write_manifest_template(tmp_path, force=True)
    assert n == 2
    data = yaml.safe_load((tmp_path / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    paths = [a["path"] for a in data["volumes"][0]["articles"]]
    assert paths == ["a.pdf", "b.pdf"]
    assert data["volumes"][0]["cover_pdf"] == "covers/_sr_book_placeholder_cover.pdf"


def test_init_scan_recursive_finds_subdir(tmp_path: Path) -> None:
    sub = tmp_path / "nested"
    sub.mkdir()
    _write_one_page_pdf(sub / "x.pdf")
    _, n = write_manifest_template(tmp_path, force=True, recursive=True)
    assert n == 1
    data = yaml.safe_load((tmp_path / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert data["volumes"][0]["articles"][0]["path"] == "nested/x.pdf"


def test_init_shallow_skips_subdir(tmp_path: Path) -> None:
    sub = tmp_path / "nested"
    sub.mkdir()
    _write_one_page_pdf(sub / "x.pdf")
    _, n = write_manifest_template(tmp_path, force=True, recursive=False)
    assert n == 0


def test_init_no_scan_static(tmp_path: Path) -> None:
    _write_one_page_pdf(tmp_path / "a.pdf")
    _, n = write_manifest_template(tmp_path, force=True, scan=False)
    assert n == 0
    data = yaml.safe_load((tmp_path / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert data["book"]["title"] == "示例书名"
