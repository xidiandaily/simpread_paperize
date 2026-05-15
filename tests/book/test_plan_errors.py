"""plan 错误路径与 CLI 退出码。"""

import yaml
from pathlib import Path
from pypdf import PdfWriter
from typer.testing import CliRunner

from simpread_paperize.book_cli import app


def _write_min_pdf(path: Path, pages: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=612, height=792)
    with path.open("wb") as f:
        w.write(f)


def _runner() -> CliRunner:
    return CliRunner()


def test_plan_missing_article_file(tmp_path: Path) -> None:
    mf = tmp_path / "manifest.yaml"
    mf.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "book": {"title": "t", "trace_header": "h"},
                "volumes": [
                    {
                        "cover_pdf": "c.pdf",
                        "articles": [{"title": "X", "path": "missing.pdf"}],
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    _write_min_pdf(tmp_path / "c.pdf")
    r = _runner().invoke(app, ["plan", "-m", str(mf)])
    assert r.exit_code == 2


def test_plan_missing_cover(tmp_path: Path) -> None:
    mf = tmp_path / "manifest.yaml"
    mf.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "book": {"title": "t", "trace_header": "h"},
                "volumes": [
                    {
                        "cover_pdf": "nocover.pdf",
                        "articles": [],
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    r = _runner().invoke(app, ["plan", "-m", str(mf)])
    assert r.exit_code == 2
