"""plan 成功路径与 plan.json。"""

import json
from pathlib import Path

import yaml

from simpread_paperize.book.plan_cmd import build_plan_from_manifest, load_manifest


def _fixture_minimal(tmp_path: Path):
    (tmp_path / "covers").mkdir()
    (tmp_path / "articles").mkdir()
    from pypdf import PdfWriter

    def w(rel: str, pages: int = 1) -> None:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=612, height=792)
        with p.open("wb") as f:
            writer.write(f)

    w("covers/c1.pdf", 1)
    w("articles/a.pdf", 2)
    w("articles/b.pdf", 1)
    data = {
        "schema_version": 1,
        "book": {"title": "t", "trace_header": "h"},
        "max_pages_per_volume": 20,
        "toc_pages_per_volume": 1,
        "volumes": [
            {
                "cover_pdf": "covers/c1.pdf",
                "articles": [
                    {"title": "A", "path": "articles/a.pdf"},
                    {"title": "B", "path": "articles/b.pdf"},
                ],
            }
        ],
    }
    mf = tmp_path / "manifest.yaml"
    mf.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return mf


def test_plan_json_matches_volume_plan(tmp_path: Path) -> None:
    mf = _fixture_minimal(tmp_path)
    model = load_manifest(mf)
    plan = build_plan_from_manifest(model)
    assert plan.success
    d = plan.to_json_dict()
    assert d["success"] is True
    assert len(d["volumes"]) == 1
    vol = d["volumes"][0]
    assert vol["total_pages"] == 1 + 1 + 2 + 1
    arts = vol["articles"]
    assert arts[0]["start_page"] == 3
    assert arts[1]["start_page"] == 5


def test_plan_json_round_trip_write(tmp_path: Path) -> None:
    mf = _fixture_minimal(tmp_path)
    model = load_manifest(mf)
    plan = build_plan_from_manifest(model)
    out = tmp_path / "plan.json"
    out.write_text(json.dumps(plan.to_json_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["volumes"][0]["articles"][0]["pages"] == 2
