"""volume_plan 贪心分卷。"""

from pathlib import Path

from simpread_paperize.book.manifest import ArticleEntry, ManifestModel, VolumeSlot
from simpread_paperize.book.volume_plan import compute_book_plan


def _model(tmp: Path, *, max_pages: int, vols: list[tuple[str, list[tuple[str, str]]]]) -> ManifestModel:
    """vols: (cover_rel, [(title, path_rel), ...])"""
    slots = [
        VolumeSlot(cover_pdf=c, articles=[ArticleEntry(t, p) for t, p in arts], slot_id=None)
        for c, arts in vols
    ]
    mf = tmp / "manifest.yaml"
    mf.write_text("x", encoding="utf-8")
    return ManifestModel(
        schema_version=1,
        book_title="b",
        trace_header="h",
        max_pages_per_volume=max_pages,
        toc_pages_per_volume=1,
        volumes=slots,
        manifest_path=mf,
    )


def test_two_articles_split_volume(tmp_path: Path) -> None:
    """单槽放不下第二篇时产生第二卷。"""
    m = _model(
        tmp_path,
        max_pages=10,
        vols=[
            ("c1.pdf", [("A", "a.pdf"), ("B", "b.pdf")]),
            ("c2.pdf", []),
        ],
    )
    # cover 1 + toc 1 = 2; A=3 -> used 5; B=7 -> 5+7=12>10 -> new vol; vol2 cover1 toc1 +7=10 OK
    plan = compute_book_plan(m, {"a.pdf": 3, "b.pdf": 7}, [1, 1])
    assert plan.success
    assert len(plan.volumes) == 2
    assert plan.volumes[0].articles[0].path == "a.pdf"
    assert plan.volumes[1].articles[0].path == "b.pdf"
    assert plan.volumes[0].total_pages == 5
    assert plan.volumes[1].total_pages == 9


def test_insufficient_slots(tmp_path: Path) -> None:
    m = _model(tmp_path, max_pages=10, vols=[("c1.pdf", [("A", "a.pdf"), ("B", "b.pdf")])])
    plan = compute_book_plan(m, {"a.pdf": 3, "b.pdf": 7}, [1])
    assert not plan.success
    assert plan.errors[0].code == "INSUFFICIENT_VOLUME_SLOTS"


def test_article_exceeds_max(tmp_path: Path) -> None:
    m = _model(tmp_path, max_pages=5, vols=[("c1.pdf", [("A", "a.pdf")])])
    plan = compute_book_plan(m, {"a.pdf": 10}, [1])
    assert not plan.success
    assert plan.errors[0].code == "ARTICLE_EXCEEDS_VOLUME_CAP"


def test_start_page_first_article(tmp_path: Path) -> None:
    m = _model(tmp_path, max_pages=100, vols=[("c1.pdf", [("A", "a.pdf")])])
    plan = compute_book_plan(m, {"a.pdf": 2}, [2])
    assert plan.success
    a = plan.volumes[0].articles[0]
    assert a.start_page == 4  # cover 2 + toc 1 + 1
