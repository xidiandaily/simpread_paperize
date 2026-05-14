---
description: "Paperize MVP 开发任务（/speckit-tasks 生成）"
---

# Tasks: Paperize MVP（简悦离线 HTML → A4 PDF）

**Input**: `specs/001-paperize-mvp/` — `plan.md`、`spec.md`、`research.md`、`data-model.md`、`contracts/`、`quickstart.md`

**约束**: 用户可见 CLI/日志为**中文**；不实现 Web UI；不实现 Docker（仅文档/结构预留）；优先 MVP（US1 + US3 + US4 + US6）。

**格式**: 每行 `- [ ] Tnnn [P?] [USx?] …`；Setup / Foundational / Polish **无** `[USx]`；用户故事阶段 **必须** 带 `[US1]`–`[US6]`。

---

## Phase 1: Setup（项目初始化）

**目标**: `uv sync` 可用；`paperize --help` 可执行且含中文。

**独立验收（阶段）**: `uv run paperize --help` 出现中文说明；`uv sync` 无报错。

### Tasks

- [ ] T001 在仓库根创建 `pyproject.toml`：包名 `paperize`、`requires-python >= 3.11`、依赖 `typer`/`rich`/`beautifulsoup4`/`lxml`/`playwright`、开发依赖 `pytest`、脚本入口 `paperize = paperize.cli:app`；验收：`uv sync` 成功，`uv run paperize --help` 可执行且输出含中文说明
- [ ] T002 创建目录与占位文件：`src/paperize/__init__.py`、`cli.py`、`config.py`、`models.py`、`renderer.py`、`runtime_patch.js`、`cleaner/__init__.py`、`cleaner/base.py`、`cleaner/simpread.py`、`cleaner/generic.py`、`assets/styles/paperize-base.css`、`assets/styles/simpread-a4.css`、`assets/styles/generic-a4.css`、`tests/test_simpread_cleaner.py`、`tests/test_filename.py`、`tests/fixtures/.gitkeep`；验收：`uv run python -c "import paperize; import paperize.cleaner"` 无异常，`uv run pytest` 可运行（允许 0 断言）

---

## Phase 2: Foundational（阻塞所有用户故事）

**目标**: 数据模型与 Cleaner 抽象就绪。

**独立验收（阶段）**: `from paperize.models import ConvertOptions, CleanResult, ConvertResult`；`BaseCleaner` 可被继承。

### Tasks

- [ ] T003 在 `src/paperize/models.py` 用 `dataclass` 定义 `ConvertOptions`（含 `paper/margin/debug/overwrite/print_background` 及 plan 中 CLI 字段）、`CleanResult`、`ConvertResult`（字段与 `data-model.md` 一致）；验收：类型清晰、无循环 import、他模块可引用
- [ ] T004 在 `src/paperize/cleaner/base.py` 定义 `BaseCleaner`：`match(html: str) -> bool`、`clean(html: str, source_path: Path | None = None) -> CleanResult`；验收：`SimpreadCleaner`/`GenericCleaner` 可继承，类型注解完整
- [ ] T016 [P] 在 `src/paperize/filename.py`（或 `config.py` 中同模块函数，路径固定一处）实现 `safe_filename(title: str) -> str`：保留中文、去除 Windows 非法字符、限长、空→`untitled`、去尾部空格与点；验收：`tests/test_filename.py` 覆盖非法字符/中文/空串/尾部点，`uv run pytest tests/test_filename.py` 通过

**Checkpoint**: 完成后可并行推进 US3（Cleaner）与后续 US4 样式文件填充。

---

## Phase 3: User Story 3 — Simpread 识别与清洗（Priority: P1）

**Story**: 自动识别简悦 HTML，提取标题/正文，DOM cleanup，输出标准 HTML（见 `spec.md` US3）。

**独立测试**: 对 `tests/fixtures/` 或裁剪自 `example_html/` 的片段运行 `choose_cleaner` + `clean`，断言无 `toc`/`sr-rd-mult-avatar`/`script`，正文保留。

### Tasks

- [ ] T005 [US3] 在 `src/paperize/cleaner/simpread.py` 实现 `SimpreadCleaner.match`：识别 `simpread`、`sr-rd-content`、`sr-rd-title`、`sr-read`、`简悦`、`SimpRead` 等；验收：含 `sr-rd-content` 为 True、普通 HTML 为 False，`tests/test_simpread_cleaner.py` 有对应用例
- [ ] T006 [US3] 在 `src/paperize/cleaner/simpread.py` 实现标题提取：优先级 `sr-rd-title` → `<title>` → 首个 `h1` → `source_path.stem` → `Untitled`，空白规范化；验收：中文标题、空标题 fallback、pytest 覆盖
- [ ] T007 [US3] 在 `src/paperize/cleaner/simpread.py` 实现正文提取：优先 `sr-rd-content`，缺省 fallback `body`；验收：输出含正文、无 `sr-rd-content` 不崩溃，pytest 覆盖
- [ ] T008 [US3] 在 `src/paperize/cleaner/simpread.py` 实现 DOM cleanup：移除 `toc`、`toc-bg`、`read-process`、`sr-rd-crlbar`、`simpread-highlight`、`sr-snapshot-ctlbar`、`simpread-feedback`、`simpread-urlscheme`、`sr-rd-mult-avatar`、`script`、`iframe` 等；验收：清洗结果无 `toc`/`sr-rd-mult-avatar`/`<script>`，正文关键文本仍在，pytest 断言
- [ ] T009 [US3] 在 `src/paperize/cleaner/simpread.py` 的 `clean` 重建标准 HTML：`<!doctype html>`、`lang="zh-CN"`、最小 `head`（charset+title，无原简悦大段 CSS）、`body > main.paperize-document.paperize-simpread > h1.paperize-title + article.paperize-content`；验收：浏览器可打开、`h1` 为标题、正文在 `article` 内
- [ ] T010 [US3] 在 `src/paperize/cleaner/generic.py` 实现 `GenericCleaner`：非简悦时 `body` 正文、删 `script`/`iframe`、重建标准 HTML（如 `paperize-generic` class）；验收：普通最小 HTML 不崩溃，`tests/test_simpread_cleaner.py` 或 `tests/test_generic_cleaner.py` 有基本用例
- [ ] T011 [US3] 在 `src/paperize/cleaner/__init__.py` 实现 `choose_cleaner(html: str) -> BaseCleaner`：先 `SimpreadCleaner` 再 `GenericCleaner`；验收：简悦样例选前者、普通 HTML 选后者，pytest 覆盖

**Checkpoint**: US3 独立完成 — 无 Playwright 也可单测清洗结果。

---

## Phase 4: User Story 4 — A4 打印样式（Priority: P1）

**Story**: 打印 CSS 满足 A4、边距、正文字体与 img/table/pre/blockquote（见 `spec.md` US4）。

**独立测试**: 打开 `assets/styles/*.css` 与 debug 导出 CSS，确认含 `@page` 与关键选择器。

### Tasks

- [ ] T012 [P] [US4] 在 `src/paperize/assets/styles/paperize-base.css` 与 `src/paperize/assets/styles/generic-a4.css` 编写 A4 基础打印规则：`@page` A4、默认 margin 14mm、`body`/版心、`h1`/`p`、`img` max-width、`pre` 换行、`table`/`blockquote`、中文友好字体栈；验收：两文件存在，含 `@page` 与 img/pre/table/blockquote 相关规则
- [ ] T013 [P] [US4] 在 `src/paperize/assets/styles/simpread-a4.css` 编写简悦标签打印重置：`sr-read`/`sr-rd-content`/`sr-rd-mult`/`sr-rd-mult-content` 块级化，`sr-rd-mult-avatar` 与目录/控制栏/反馈层 `display:none`，`sr-rd-desc` 可隐藏；验收：文件存在且含对 `sr-rd-mult`、`sr-rd-mult-avatar`、`sr-rd-content` 的明确规则
- [ ] T014 [US4] 在 `src/paperize/runtime_patch.js` 实现轻量运行时修补：`img[data-src]`/`img[data-original]`→`src`、删空 `p`、给过宽 `table` 加 class；验收：文件存在、无重 DOM 清洗逻辑、可由 `renderer.py` 注入执行

---

## Phase 5: User Story 1 — 单文件 HTML → PDF（Priority: P1）MVP

**Story**: `paperize input.html -o output.pdf` 端到端（见 `spec.md` US1）。

**独立测试**: `uv run paperize tests/fixtures/x.html -o /tmp/out.pdf` 生成可读 PDF；失败路径中文无大段原文。

### Tasks

- [ ] T015 [US1] 在 `src/paperize/renderer.py` 实现 `render_pdf(cleaned_html_path, output_pdf_path, options, css_paths)`：Playwright Chromium、`page.goto(Path.as_uri())`、`emulated_media=print`、注入 CSS、`runtime_patch.js`、等待图片、`page.pdf`（A4、margin、`print_background`、`prefer_css_page_size`）；验收：可由 fixture `cleaned.html` 生成 PDF，失败抛明确异常供上层转中文
- [ ] T017 [US1] 在 `src/paperize/` 新增服务模块（如 `src/paperize/convert.py`）实现 `convert_one(input_path, output_path, options) -> ConvertResult`：读源、`choose_cleaner`、`clean`、写临时 `cleaned.html`（debug 复制到 `.paperize-debug/<slug>/`）、调 `render_pdf`；验收：单文件可出 PDF；目标已存在且未 `--overwrite` 时拒绝（中文）；错误信息中文、不打印大段原文
- [ ] T018 [US1] 在 `src/paperize/cli.py` 绑定 Typer：`paperize INPUT -o/--output ...`、`--debug`、`--overwrite`；中文进度/成功路径；失败中文原因、默认不打印完整 traceback（`--debug` 可打印）；验收：`uv run paperize … -o …` 可用，`--help` 中文可读

**Checkpoint**: **MVP 核心闭环**（US1+US3+US4+US6 主路径）应已达成。

---

## Phase 6: User Story 2 — 批量目录转换（Priority: P2）

**Story**: `paperize ./dir --out ./pdf --recursive`（见 `spec.md` US2）。

**独立测试**: 多文件目录，部分失败时仍产出其余 PDF，stdout 中文汇总。

### Tasks

- [ ] T019 [US2] 在 `src/paperize/cli.py`（或 `src/paperize/batch.py`）实现目录输入：收集 `.html`/`.htm`，`--recursive` 控制递归，`--out` 必填于目录模式；验收：非递归仅当前目录、递归含子目录、0 文件时中文提示
- [ ] T020 [US2] 实现批量转换：每文件独立 try/except、失败不中断；汇总总数/成功/失败/输出目录；输出名 `safe_filename(title)` 或 stem、碰撞后缀；已存在 PDF 默认跳过或失败并提示 `--overwrite`；验收：中文失败列表、与 `contracts/cli.md` 一致

---

## Phase 7: User Story 5 — Debug 模式（Priority: P2）

**Story**: `--debug` 落盘中间产物（见 `spec.md` US5）。

**独立测试**: `--debug` 后存在 `original.html`、`cleaned.html`、CSS 副本、`render.log`，终端打印目录 URI/路径。

### Tasks

- [ ] T021 [US5] 在 `convert_one`/`renderer` 协作路径实现 debug：`.paperize-debug/<slug>/` 写入 `original.html`、`cleaned.html`、拷贝 `paperize-base.css` 与本次 `simpread-a4.css` 或 `generic-a4.css`、`render.log`（关键步骤）；验收：CLI 中文打印 debug 目录，`cleaned.html` 可被浏览器打开，`render.log` 非空关键行

---

## Phase 8: Polish & 横切（US6 文档与测试加固）

**Story**: 中文 README、开发命令、测试全绿（`spec.md` US6 与质量门禁）。

### Tasks

- [ ] T022 在仓库根 `README.md`（中文）撰写：产品说明、解决的问题、`uv` 安装、`playwright install chromium`、单文件/批量示例、`--debug`、当前限制（无 Web UI/Docker）；验收：新用户仅依 README 可跑通 MVP 命令
- [ ] T023 补强 `tests/test_simpread_cleaner.py` 等：覆盖 `match`、标题、DOM cleanup、`choose_cleaner`、`GenericCleaner`、与 T016 已有关联测试合并后 `uv run pytest` 全通过；验收：`uv run pytest` 0 failure
- [ ] T024 在 `README.md` 增加开发命令小节：`uv sync`、`uv run playwright install chromium`、`uv run paperize --help`、`uv run pytest`；验收：命令可复制、表述清晰

---

## Dependencies（用户故事顺序）

```text
Phase1 → Phase2 → US3 → US4 → US1(MVP) → US2 → US5 → Polish
```

- **US1** 依赖 **US3**（清洗输出）、**US4**（CSS/JS）、**Phase2**（models/registry/filename）。
- **US2** 依赖 **US1**（单文件转换逻辑复用）。
- **US5** 依赖 **US1**（管线与 CLI 已有 `--debug` 开关）。
- **US6** 横切：贯穿 T001–T024；T022/T024 集中文档。

## Parallel opportunities

- **T016** 可与 **T004** 并行（均在 T003 之后，不同文件）。
- **T012**、**T013** 可并行（不同 CSS 文件）。
- **T010** 可与 **T005–T008** 并行开发，**T011** 前需完成 T005 与 T010。

## Implementation strategy

1. 完成 Phase1–2 → US3（T005–T011）→ US4（T012–T014）。
2. 打通 **US1**（T015→T017→T018）作为 **MVP 演示点**；此时应用 `example_html/` 或 `tests/fixtures` 做一次手工验收。
3. 追加 US2（T019–T020）、US5（T021），最后 Polish（T022–T024）。

## 任务与 spec 用户故事映射

| 任务 | 主要 US |
|------|---------|
| T001–T002, T003–T004 | Setup / Foundation |
| T005–T011 | US3 |
| T012–T014 | US4 |
| T015–T018 | US1 |
| T019–T020 | US2 |
| T021 | US5 |
| T016 | Foundation（文件名，服务 US2） |
| T022–T024 | US6 / 质量 |

## 格式校验

- 共 **24** 条 checklist 任务 **T001–T024**。
- 用户故事阶段任务均含 **`[USn]`** 标签；Setup/Foundational/Polish 无故事标签。
- **T016** 带 **`[P]`**（可与 T004 并行）。
- **T012、T013** 带 **`[P]`**（US4 内并行）。

---

**生成路径**: `specs/001-paperize-mvp/tasks.md`（由 `/speckit-tasks` 根据 `setup-tasks.sh --json` 与 `spec.md` 用户故事重组生成）。
