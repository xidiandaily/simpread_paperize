"""build 烟测：页数、源文件不变。"""

from pathlib import Path

import yaml
from typer.testing import CliRunner

from simpread_paperize.book_cli import app


def _write_min_pdf(path: Path, pages: int = 1) -> None:
    from pypdf import PdfWriter

    path.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=612, height=792)
    with path.open("wb") as f:
        w.write(f)


def test_build_merge_smoke(tmp_path: Path) -> None:
    _write_min_pdf(tmp_path / "covers" / "c1.pdf")
    _write_min_pdf(tmp_path / "articles" / "a.pdf", pages=2)
    mf = tmp_path / "manifest.yaml"
    mf.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "book": {"title": "t", "trace_header": "hdr"},
                "max_pages_per_volume": 50,
                "toc_pages_per_volume": 1,
                "volumes": [
                    {
                        "cover_pdf": "covers/c1.pdf",
                        "articles": [{"title": "篇A", "path": "articles/a.pdf"}],
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    assert runner.invoke(app, ["plan", "-m", str(mf), "--quiet"]).exit_code == 0
    src = (tmp_path / "articles" / "a.pdf").read_bytes()
    outd = tmp_path / "out"
    r = runner.invoke(app, ["build", "-m", str(mf), "-o", str(outd)])
    assert r.exit_code == 0
    out_pdf = outd / "volume-01.pdf"
    assert out_pdf.is_file()
    from pypdf import PdfReader

    reader = PdfReader(out_pdf.open("rb"))
    assert len(reader.pages) >= 3
    assert (tmp_path / "articles" / "a.pdf").read_bytes() == src
