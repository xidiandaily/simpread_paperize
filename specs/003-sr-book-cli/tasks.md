# Tasks: SR Book CLI（`sr_book` 成书）

**Input**: Design documents from `specs/003-sr-book-cli/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md), [quickstart.md](./quickstart.md)

**Tests**: 本特性任务单显式包含单元/集成测试（分卷、`plan`、路径、`index`、错误路径、`build` 烟测）；**不**要求改动 `sr_paperize` 渲染管线，**不**引入 Web 服务。

**Organization**: 按 `spec.md` 用户故事优先级分阶段；实现前完成 Setup + Foundational。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成的前置依赖）
- **[Story]**: 仅用户故事阶段使用 `[US1]`…`[US4]`，对应 spec 中 P1–P4

## Phase 1: Setup（依赖与包骨架）

**Purpose**: 注册 CLI、锁依赖、建立 `book` 与测试目录

- [x] T001 Add `pypdf`, `reportlab`, `pyyaml` to `[project]` dependencies and register `sr_book = "simpread_paperize.book_cli:app"` under `[project.scripts]` in `pyproject.toml`, then run `uv lock` at repository root to refresh `uv.lock`
- [x] T002 [P] Create `src/simpread_paperize/book/__init__.py` exporting the `book` subpackage
- [x] T003 [P] Create `tests/book/__init__.py` to host book-related pytest modules
- [x] T004 [P] Add `tests/fixtures/book/README.md` describing offline minimal PDF fixtures (paths, how tests generate or copy them; no network)

---

## Phase 2: Foundational（阻塞所有用户故事）

**Purpose**: manifest 路径规则、YAML 解析与校验、分卷核心算法、四子命令 Typer 骨架

**⚠️ CRITICAL**: 未完成本阶段前不得实现各故事的业务闭环

- [x] T005 Implement `manifest_dir`-relative resolution and rejection of `..`/escape paths in `src/simpread_paperize/book/paths.py` per `specs/003-sr-book-cli/data-model.md`
- [x] T006 Implement YAML load/dump, field validation, and typed manifest model (incl. global article order from `volumes[].articles`) in `src/simpread_paperize/book/manifest.py` aligned with `specs/003-sr-book-cli/data-model.md` and `specs/003-sr-book-cli/contracts/cli.md`
- [x] T007 Implement greedy volume packing, per-volume `total_pages`, and per-article `start_page` in `src/simpread_paperize/book/volume_plan.py` (single implementation reused by plan/build) per `specs/003-sr-book-cli/data-model.md`
- [x] T008 [P] Add unit tests for split boundaries, `INSUFFICIENT_VOLUME_SLOTS`, and non-splitting of articles in `tests/book/test_volume_plan.py`
- [x] T009 [P] Add unit tests for allowed/blocked relative paths in `tests/book/test_manifest_paths.py` against `src/simpread_paperize/book/paths.py` and manifest loading in `src/simpread_paperize/book/manifest.py`
- [x] T010 Create Typer application `app` with four subcommands `init`, `index`, `plan`, `build` (stub handlers, Chinese `--help` strings, shared `Console` pattern like `src/simpread_paperize/cli.py`) in `src/simpread_paperize/book_cli.py`

**Checkpoint**: `uv run sr_book --help` 与四子命令 `--help` 可运行；`volume_plan` 与路径规则有绿灯单测

---

## Phase 3: User Story 1 — 初始化 manifest（Priority: P1）🎯 MVP

**Goal**: `sr_book init` 在目标目录生成可编辑的 `manifest.yaml` 模板（含 `schema_version`、`book`、`max_pages_per_volume`、`toc_pages_per_volume`、`volumes` 占位）

**Independent Test**: 在临时目录执行 `init` 后存在模板文件；默认拒绝覆盖、`--force` 可覆盖

### Implementation for User Story 1

- [x] T011 [US1] Implement template content and `init` target dir / `--force` logic in `src/simpread_paperize/book/init_manifest.py`, wire `init` subcommand in `src/simpread_paperize/book_cli.py`
- [x] T012 [US1] Add `tests/book/test_init.py` asserting generated YAML keys and overwrite behavior without touching `src/simpread_paperize/cli.py` (sr_paperize 入口保持不变)

**Checkpoint**: 仅合入 US1 亦可演示「脚手架 manifest」价值

---

## Phase 4: User Story 2 — `index` 编号与 manifest 回写（Priority: P2）

**Goal**: 按 manifest 全局篇序添加 `1_`、`2_`…前缀；`--dry-run` 零副作用；回写 YAML 路径；不触碰未列出文件

**Independent Test**: fixture PDF + manifest；对比 dry-run 与实跑磁盘与 YAML

### Implementation for User Story 2

- [x] T013 [US2] Implement ordered rename plan, filesystem renames, and manifest rewrite with `--dry-run` guard in `src/simpread_paperize/book/index_rename.py`, wire `index` subcommand in `src/simpread_paperize/book_cli.py`
- [x] T014 [US2] Add `tests/book/test_index_rewrite.py` covering dry-run vs commit, manifest path updates, and that non-listed sibling files are unchanged under `tests/fixtures/book/` (or tmp paths)

**Checkpoint**: `index` 可独立验收，不依赖 `build`

---

## Phase 5: User Story 3 — `plan` 表格 + JSON + `plan.json`（Priority: P3）

**Goal**: 读取 manifest 与各 PDF 页数；stdout 人类表格；结构化 JSON；`--plan-out` 默认 `{manifest_dir}/plan.json`；失败路径非零退出；**不**写合集 PDF

**Independent Test**: 合法 manifest 产出 `plan.json`；缺封面 / 单篇超长 / 路径不存在触发 `contracts` 中错误码与退出码

### Implementation for User Story 3

- [x] T015 [US3] Implement page counting (pypdf), plan orchestration, Rich/stdout table, JSON serialization, and `plan.json` writer in `src/simpread_paperize/book/plan_cmd.py`, wire `plan` subcommand in `src/simpread_paperize/book_cli.py` per `specs/003-sr-book-cli/contracts/cli.md`

### Tests for User Story 3

- [x] T016 [P] [US3] Add `tests/book/test_plan_output.py` asserting `plan.json` schema and consistency with `volume_plan.py` for golden fixture manifests under `tests/fixtures/book/`
- [x] T017 [P] [US3] Add `tests/book/test_plan_errors.py` for missing cover (`FILE_NOT_FOUND` / 中文提示), `ARTICLE_EXCEEDS_VOLUME_CAP`, and missing article path; assert non-zero exit via Typer runner in `tests/book/test_plan_errors.py`

**Checkpoint**: `plan` 可独立 CI 验证；与后续 `build` 共用 `volume_plan.py`

---

## Phase 6: User Story 4 — `build` 合并与版式（Priority: P4）

**Goal**: 封面 → 目录页 → 篇合并；篇级书签；页眉 `trace_header`；左下「当前页/卷总页」；源单篇 PDF 只读；`--overwrite` / `--temp-dir`

**Independent Test**: fixture 小 PDF 多卷；`pypdf` 读取 outline 与页数抽样；源文件 mtime/size 不变

### Implementation for User Story 4

- [x] T018 [P] [US4] Implement printable TOC PDF (篇名 + 起始页，不含封面/目录行) in `src/simpread_paperize/book/toc_pdf.py` using ReportLab per `specs/003-sr-book-cli/research.md`
- [x] T019 [P] [US4] Implement cover append, TOC insert, article merge, discard nested bookmarks, add article-level outline, and header/footer overlay via pypdf in `src/simpread_paperize/book/merge_build.py`
- [x] T020 [US4] Wire `build` subcommand (`--manifest`, `--plan`, `--output-dir`, `--overwrite`, `--temp-dir`) in `src/simpread_paperize/book_cli.py`, reusing `volume_plan.py` (or validated `plan.json`) per `specs/003-sr-book-cli/contracts/cli.md`; **do not** modify `src/simpread_paperize/renderer.py` or Playwright pipeline

### Tests for User Story 4

- [x] T021 [US4] Add `tests/book/test_build_merge.py` smoke-testing merged page count, single-level outlines, and that source fixture PDF bytes are unchanged when output is written to tmpdir (uses `tests/fixtures/book/`)

**Checkpoint**: 四子命令闭环可本地跑通；`sr_paperize` 行为不变

---

## Phase 7: Polish & 文档对齐

**Purpose**: quickstart / README 与契约一致；最小端到端示例

- [x] T022 Update `specs/003-sr-book-cli/quickstart.md` with copy-pasteable minimal E2E (init → edit note → index → plan → build) referencing `tests/fixtures/book/` sample PDFs and exact flags from `specs/003-sr-book-cli/contracts/cli.md`
- [x] T023 [P] Add `sr_book` section (one paragraph + link to `specs/003-sr-book-cli/quickstart.md`) in `README.md` at repository root
- [x] T024 [P] If CLI flags or error codes differ after implementation, update `specs/003-sr-book-cli/contracts/cli.md` and cross-links in `specs/003-sr-book-cli/data-model.md` error tables to stay authoritative
- [x] T025 Manually run the E2E block from `specs/003-sr-book-cli/quickstart.md` with `uv run sr_book` and fix gaps (document result in PR description; no Web service)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**：无上游依赖，可立即开始
- **Phase 2 (Foundational)**：依赖 Phase 1；**阻塞** US1–US4
- **Phase 3–6 (US1→US4)**：均依赖 Phase 2；默认按 P1→P4 串行以降低集成风险；US3/US4 强依赖 `volume_plan.py` 与 manifest 模型
- **Phase 7 (Polish)**：依赖计划交付的 CLI 行为已稳定

### User Story Dependencies

| Story | 依赖 | 说明 |
|-------|------|------|
| US1 | Phase 2 | 仅需模板与 Typer 壳 |
| US2 | Phase 2 + US1 产出的 manifest 字段约定（可与 US1 串行） | 实作可与 US1 同分支连续提交 |
| US3 | Phase 2 | 可与 US2 并行开发但集成顺序建议 US2→US3 |
| US4 | Phase 2 + US3 推荐（`plan.json` 烟测） | `build` 必须与 `plan` 分页规则一致 |

### Parallel Opportunities

- Phase 1：`T002`–`T004` 可并行
- Phase 2：完成 `T005`–`T007` 后，`T008` 与 `T009` 可并行编写不同测试文件
- Phase 5：`T016` 与 `T017` 在 `T015` 完成后可由不同人并行编写，pytest 可同批运行
- Phase 6：`T018`（TOC）与 `T019`（merge/overlay）可并行开发，于 `T020` 汇合后再跑 `T021`
- Phase 7：`T023` 与 `T024` 可并行

### Parallel Example: User Story 4（实现阶段）

```text
# 不同文件并行：
T018  src/simpread_paperize/book/toc_pdf.py
T019  src/simpread_paperize/book/merge_build.py
# 汇合：
T020  src/simpread_paperize/book_cli.py 中 build 接线
```

### Parallel Example: Phase 5 测试（在 T015 完成后）

```text
pytest tests/book/test_plan_output.py tests/book/test_plan_errors.py -q
```

---

## Implementation Strategy

### MVP First（仅 US1）

1. 完成 Phase 1 + Phase 2  
2. 完成 Phase 3（US1）→ 用 `tests/book/test_init.py` 验证  
3. 演示「可生成 manifest 模板」即可对外说明进度

### Incremental Delivery

1. Setup + Foundational → 算法与契约地基稳固  
2. +US1 → +US2 → +US3 → +US4，每阶段均有独立测试与 CLI 检查点  
3. Phase 7 保证 `quickstart.md` / `README.md` / `contracts/cli.md` 与真实命令一致  

### 显式排除范围

- **不得**修改 `src/simpread_paperize/cli.py` 中 `sr_paperize` 行为（除非仅为并排文档说明，代码路径以「不改渲染」为准）  
- **不得**引入默认联网 Web 服务或远程日志上报

---

## Notes

- 任务描述中的路径均为仓库内相对路径；Windows/macOS 以 `pathlib` 验证  
- `[P]` 仅用于无文件冲突、无逻辑先后依赖的项  
- 每个用户故事结束建议在 PR 中附该 story 的 **Independent Test** 命令

---

## Task counts

| 阶段 | 任务数 |
|------|--------|
| Phase 1 Setup | 4 |
| Phase 2 Foundational | 6 |
| Phase 3 US1 | 2 |
| Phase 4 US2 | 2 |
| Phase 5 US3 | 3（1 实现 + 2 测试 `[P]`） |
| Phase 6 US4 | 4（3 实现 + 1 测试） |
| Phase 7 Polish | 4 |
| **Total** | **25** |
