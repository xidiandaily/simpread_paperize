"""分卷贪心：与 plan / build 共用。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from simpread_paperize.book.manifest import ArticleEntry, ManifestModel


@dataclass
class PlannedArticle:
    title: str
    path: str
    pages: int
    start_page: int


@dataclass
class PlannedVolume:
    volume_index: int
    cover_pdf: str
    cover_pages: int
    toc_pages: int
    total_pages: int
    articles: list[PlannedArticle] = field(default_factory=list)


@dataclass
class PlanErrorEntry:
    code: str
    message: str
    path: str | None = None


@dataclass
class BookPlan:
    manifest_path: str
    max_pages_per_volume: int
    toc_pages_per_volume: int
    volumes: list[PlannedVolume] = field(default_factory=list)
    success: bool = True
    errors: list[PlanErrorEntry] = field(default_factory=list)

    def to_json_dict(self) -> dict:
        return {
            "schema_version": 1,
            "manifest_path": self.manifest_path,
            "max_pages_per_volume": self.max_pages_per_volume,
            "toc_pages_per_volume": self.toc_pages_per_volume,
            "success": self.success,
            "volumes": [
                {
                    "volume_index": v.volume_index,
                    "cover_pdf": v.cover_pdf,
                    "cover_pages": v.cover_pages,
                    "toc_pages": v.toc_pages,
                    "total_pages": v.total_pages,
                    "articles": [
                        {
                            "title": a.title,
                            "path": a.path,
                            "pages": a.pages,
                            "start_page": a.start_page,
                        }
                        for a in v.articles
                    ],
                }
                for v in self.volumes
            ],
            "errors": [{"code": e.code, "message": e.message, "path": e.path} for e in self.errors],
        }


def compute_book_plan(
    model: ManifestModel,
    article_pages: dict[str, int],
    volume_cover_pages: list[int],
) -> BookPlan:
    """
    贪心装箱：全局篇序见 ``ManifestModel.global_articles()``。

    ``volume_cover_pages[i]`` 对应 ``model.volumes[i].cover_pdf`` 的页数。
    """
    max_p = model.max_pages_per_volume
    toc = model.toc_pages_per_volume
    slots_n = len(model.volumes)
    if len(volume_cover_pages) != slots_n:
        raise ValueError("volume_cover_pages 长度必须与 volumes 一致。")

    def fail(code: str, message: str, path: str | None = None) -> BookPlan:
        return BookPlan(
            manifest_path=str(model.manifest_path),
            max_pages_per_volume=max_p,
            toc_pages_per_volume=toc,
            success=False,
            errors=[PlanErrorEntry(code=code, message=message, path=path)],
        )

    arts_q: deque[ArticleEntry] = deque(model.global_articles())
    out_vols: list[PlannedVolume] = []
    slot = 0
    vol_index = 1

    while arts_q:
        if slot >= slots_n:
            return fail(
                "INSUFFICIENT_VOLUME_SLOTS",
                "装箱所需卷数超过 manifest 中 volumes 条目数，请追加带 cover_pdf 的卷。",
                None,
            )
        cover_p = volume_cover_pages[slot]
        cover_rel = model.volumes[slot].cover_pdf
        used = cover_p + toc
        batch: list[PlannedArticle] = []
        while arts_q:
            art = arts_q[0]
            p = article_pages.get(art.path)
            if p is None:
                return fail("MANIFEST_SCHEMA", f"缺少篇目页数：{art.path}", art.path)
            if p > max_p:
                return fail(
                    "ARTICLE_EXCEEDS_VOLUME_CAP",
                    f"篇目页数 {p} 超过每卷上限 {max_p}，请拆篇或提高 max_pages_per_volume。",
                    art.path,
                )
            if used + p > max_p:
                break
            start_pg = used + 1
            batch.append(PlannedArticle(title=art.title, path=art.path, pages=p, start_page=start_pg))
            used += p
            arts_q.popleft()
        if batch:
            out_vols.append(
                PlannedVolume(
                    volume_index=vol_index,
                    cover_pdf=cover_rel,
                    cover_pages=cover_p,
                    toc_pages=toc,
                    total_pages=used,
                    articles=batch,
                )
            )
            vol_index += 1
            slot += 1
        else:
            # 空卷无法容纳队首篇：换下一个封面槽位
            slot += 1
            if slot >= slots_n:
                head = arts_q[0]
                hp = article_pages[head.path]
                if hp > max_p:
                    return fail(
                        "ARTICLE_EXCEEDS_VOLUME_CAP",
                        f"篇目页数 {hp} 超过每卷上限 {max_p}。",
                        head.path,
                    )
                return fail(
                    "ARTICLE_EXCEEDS_VOLUME_CAP",
                    "在现有封面与目录占位下，无法在任一卷中容纳下一整篇；请拆篇或提高 max_pages_per_volume。",
                    head.path,
                )

    return BookPlan(
        manifest_path=str(model.manifest_path),
        max_pages_per_volume=max_p,
        toc_pages_per_volume=toc,
        volumes=out_vols,
        success=True,
        errors=[],
    )
