"""manifest.yaml 加载、校验与写回。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from simpread_paperize.book.paths import PathEscapeError, resolve_under_manifest_dir


class ManifestError(ValueError):
    """结构或字段非法。"""


@dataclass
class ArticleEntry:
    title: str
    path: str


@dataclass
class VolumeSlot:
    cover_pdf: str
    articles: list[ArticleEntry] = field(default_factory=list)
    slot_id: str | int | None = None


@dataclass
class ManifestModel:
    schema_version: int
    book_title: str
    trace_header: str
    max_pages_per_volume: int
    toc_pages_per_volume: int
    volumes: list[VolumeSlot]
    manifest_path: Path

    @property
    def manifest_dir(self) -> Path:
        return self.manifest_path.parent.resolve()

    def global_articles(self) -> list[ArticleEntry]:
        out: list[ArticleEntry] = []
        for vol in self.volumes:
            out.extend(vol.articles)
        return out

    def to_yaml_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book": {"title": self.book_title, "trace_header": self.trace_header},
            "max_pages_per_volume": self.max_pages_per_volume,
            "toc_pages_per_volume": self.toc_pages_per_volume,
            "volumes": [
                {
                    **({"id": vs.slot_id} if vs.slot_id is not None else {}),
                    "cover_pdf": vs.cover_pdf,
                    "articles": [{"title": a.title, "path": a.path} for a in vs.articles],
                }
                for vs in self.volumes
            ],
        }


def _require_str(d: dict[str, Any], key: str, ctx: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ManifestError(f"{ctx} 缺少或非法字符串字段 {key!r}。")
    return v.strip()


def _optional_int(d: dict[str, Any], key: str, default: int, ctx: str) -> int:
    v = d.get(key, default)
    if v is None:
        return default
    if not isinstance(v, int) or isinstance(v, bool):
        raise ManifestError(f"{ctx} 字段 {key!r} 必须为整数。")
    return int(v)


def parse_manifest_dict(data: dict[str, Any], manifest_path: Path) -> ManifestModel:
    ctx = "manifest"
    if not isinstance(data, dict):
        raise ManifestError("根节点必须为 YAML mapping。")
    schema_version = data.get("schema_version", 1)
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise ManifestError("schema_version 必须为整数。")
    book = data.get("book")
    if not isinstance(book, dict):
        raise ManifestError("缺少 book 映射。")
    title = _require_str(book, "title", "book")
    trace = _require_str(book, "trace_header", "book")
    max_pages = _optional_int(data, "max_pages_per_volume", 400, ctx)
    toc_pages = _optional_int(data, "toc_pages_per_volume", 1, ctx)
    if max_pages < 1:
        raise ManifestError("max_pages_per_volume 必须 >= 1。")
    if toc_pages < 1:
        raise ManifestError("toc_pages_per_volume 必须 >= 1。")
    vols_raw = data.get("volumes")
    if not isinstance(vols_raw, list) or not vols_raw:
        raise ManifestError("volumes 必须为非空列表。")
    mdir = manifest_path.parent
    volumes: list[VolumeSlot] = []
    for i, vr in enumerate(vols_raw):
        if not isinstance(vr, dict):
            raise ManifestError(f"volumes[{i}] 必须为 mapping。")
        cover = _require_str(vr, "cover_pdf", f"volumes[{i}]")
        try:
            resolve_under_manifest_dir(mdir, cover)
        except PathEscapeError as exc:
            raise ManifestError(str(exc)) from exc
        slot_id = vr.get("id")
        if slot_id is not None:
            if isinstance(slot_id, bool) or not isinstance(slot_id, (str, int)):
                raise ManifestError(f"volumes[{i}].id 非法。")
        arts_raw = vr.get("articles", []) or []
        if not isinstance(arts_raw, list):
            raise ManifestError(f"volumes[{i}].articles 必须为列表。")
        arts: list[ArticleEntry] = []
        for j, ar in enumerate(arts_raw):
            if not isinstance(ar, dict):
                raise ManifestError(f"volumes[{i}].articles[{j}] 非法。")
            t = _require_str(ar, "title", f"articles[{j}]")
            p = _require_str(ar, "path", f"articles[{j}]")
            if not p.lower().endswith(".pdf"):
                raise ManifestError(f"篇目路径必须为 .pdf：{p!r}")
            try:
                resolve_under_manifest_dir(mdir, p)
            except PathEscapeError as exc:
                raise ManifestError(str(exc)) from exc
            arts.append(ArticleEntry(title=t, path=p))
        volumes.append(VolumeSlot(cover_pdf=cover, articles=arts, slot_id=slot_id))
    return ManifestModel(
        schema_version=schema_version,
        book_title=title,
        trace_header=trace,
        max_pages_per_volume=max_pages,
        toc_pages_per_volume=toc_pages,
        volumes=volumes,
        manifest_path=manifest_path.resolve(),
    )


def load_manifest(manifest_path: Path) -> ManifestModel:
    path = manifest_path.resolve()
    if not path.is_file():
        raise ManifestError(f"找不到 manifest：{path}")
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ManifestError(f"YAML 解析失败：{exc}") from exc
    if data is None:
        raise ManifestError("manifest 为空。")
    if not isinstance(data, dict):
        raise ManifestError("manifest 根必须为 mapping。")
    return parse_manifest_dict(data, path)


def dump_manifest(model: ManifestModel) -> str:
    return yaml.safe_dump(
        model.to_yaml_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def save_manifest(model: ManifestModel) -> None:
    model.manifest_path.write_text(dump_manifest(model), encoding="utf-8")
