# Tasks: Paperize MVP（简悦离线 HTML → A4 PDF）

**Input**: `/specs/001-paperize-mvp/` 下的 `spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/`

**Prerequisites**: plan.md、spec.md（必须）；research.md、data-model.md、contracts/cli.md（已具备）

**约束**: 用户可见交互与日志使用**中文**；不实现 Web UI；不实现 Docker（仅文档/结构预留）；任务尽量可独立完成并带验收标准；优先打通 MVP（单文件 → PDF）。

## 格式说明

- `[P]`：可与同阶段无依赖任务并行（不同文件、无先后依赖）。
- 路径以仓库根为基准：`src/paperize/`、`tests/`。

---

## Phase 1：项目初始化（MVP 基础）

**目标**：`uv sync` 可安装依赖；CLI 入口可用；帮助含中文。

### T001 — 初始化 uv Python 项目

**内容**

- 创建 `pyproject.toml`：项目名 `paperize`，`requires-python >= 3.11`。
- 配置脚本入口：`paperize = paperize.cli:app`（Typer app，见 T002）。
- 运行时依赖：`typer`、`rich`、`beautifulsoup4`、`lxml`、`playwright`。
- 开发依赖：`pytest`。

**验收标准**

- `uv sync` 成功执行无报错。
- `uv run paperize --help` 可执行。
- `--help` 输出中含**中文**说明（至少包含命令用途或主要选项说明）。

**依赖**：无（首个任务）。

---

### T002 — 建立目录结构与占位模块

**内容**

创建下列路径（可先空实现或 `pass` / 最小 Typer app）：

```text
src/paperize/
├── __init__.py
├── cli.py
├── config.py
├── models.py
├── renderer.py
├── runtime_patch.js
├── cleaner/
│   ├── __init__.py
│   ├── base.py
│   ├── simpread.py
│   └── generic.py
└── assets/styles/
    ├── paperize-base.css
    ├── simpread-a4.css
    └── generic-a4.css
tests/
├── test_simpread_cleaner.py
├── test_filename.py
└── fixtures/
```

**验收标准**

- `uv run python -c "import paperize"` 及 `import paperize.cleaner` 等不报错。
- `uv run pytest` 可执行（允许 0 测试或空测试通过）。

**依赖**：T001。

---

## Phase 2：数据模型与 Cleaner 基座

**目标**：类型与抽象稳定，后续 Simpread/Generic 均可接入。

### T003 [P] — 实现 `models.py`（dataclass）

**内容**

在 `src/paperize/models.py` 定义：

- `ConvertOptions`：`paper: str = "A4"`，`margin: str = "14mm"`，`debug: bool = False`，`overwrite: bool = False`，`print_background: bool = True`；另含 spec/plan 所需字段（如 `output_pdf`、`output_dir`、`recursive`、`prefer_css_page_size` 等）以保持与 `data-model.md` 一致。
- `CleanResult`：`title`、`html`、`source_type`、`warnings: list[str]`。
- `ConvertResult`：`input_path`、`output_path`、`message`、`success`、`debug_dir`（类型与 `data-model.md` 一致）。

**验收标准**

- 类型注解清晰，字段默认值符合 plan/research。
- 其他模块可 `from paperize.models import ...` 无循环依赖问题。

**依赖**：T002。

---

### T004 — 实现 `BaseCleaner`（`cleaner/base.py`）

**内容**

- 抽象基类：`match(self, html: str) -> bool`，`clean(self, html: str, source_path: Path | None = None) -> CleanResult`。

**验收标准**

- `SimpreadCleaner`、`GenericCleaner` 可继承且不破坏 LSP。
- 完整类型提示；`pytest` 可 import 测试类。

**依赖**：T003。

---

## Phase 3：SimpreadCleaner（识别、标题、正文、清洗、标准 HTML）

**目标**：简悦 HTML 识别与清洗闭环，为渲染供稿。

### T005 — 实现 `SimpreadCleaner.match`

**内容**

关键字/片段识别（满足任一合理条件即可，需在测试中固定）：`simpread`、`sr-rd-content`、`sr-rd-title`、`sr-read`、`简悦`、`SimpRead` 等（与 spec 一致）。

**验收标准**

- 含 `sr-rd-content` 的片段/HTML 返回 `True`。
- 普通不含特征 HTML 返回 `False`。
- `tests/test_simpread_cleaner.py` 中含对应用例。

**依赖**：T004。

---

### T006 — 实现 `SimpreadCleaner` 标题提取

**内容**

优先级：`sr-rd-title` 文本 → `<title>` → 首个 `h1` → `source_path.stem` → `"Untitled"`；空白压缩与 strip。

**验收标准**

- 中文标题正确提取；多空格/换行清理。
- 全无时的 fallback 符合优先级。
- `tests/test_simpread_cleaner.py` 覆盖上述分支。

**依赖**：T005。

---

### T007 — 实现 `SimpreadCleaner` 正文提取

**内容**

优先提取 `sr-rd-content` 内 HTML；缺失时 fallback 到 `body`（或整文档兜底），不抛未捕获异常。

**验收标准**

- 输出 `CleanResult.html` 含可见正文节点。
- 无 `sr-rd-content` 时不崩溃。
- pytest 覆盖有/无 `sr-rd-content` 场景。

**依赖**：T006。

---

### T008 — 实现 Simpread DOM cleanup

**内容**

移除（或等价剥离）节点：`toc`、`toc-bg`、`read-process`、`sr-rd-crlbar`、`simpread-highlight`、`sr-snapshot-ctlbar`、`simpread-feedback`、`simpread-urlscheme`、`sr-rd-mult-avatar`、`script`、`iframe`；空 `script` 删除；保留正文段落、图、链接、代码、引用、表格。

**验收标准**

- 清洗后字符串/HTML 解析结果中不包含：`toc`（作为阅读器 UI 的 toc 容器）、`sr-rd-mult-avatar`、`script`（按需求移除脚本）。
- 正文中关键文本仍保留（对 fixture 断言子串或节点存在）。
- pytest 使用 `tests/fixtures/` 或裁剪自 `example_html/` 的小片段。

**依赖**：T007。

---

### T009 — 实现标准 HTML 重建（Simpread `clean` 输出）

**内容**

生成新文档骨架（与计划一致）：

- `<!doctype html>`，`<html lang="zh-CN">`。
- `head`：仅 `charset`、`title`（来自提取标题），**不**内联原简悦大段 CSS。
- `body` → `main.paperize-document.paperize-simpread` → `h1.paperize-title` + `article.paperize-content`（内嵌清洗后正文 DOM）。

**验收标准**

- 输出可被浏览器打开；`head` 无原简悦样式大块。
- `h1` 为标题；`article` 内为正文主体。
- pytest 快照或关键结构断言。

**依赖**：T008。

---

### T010 — 实现 `GenericCleaner`

**内容**

非简悦 HTML：`match` 恒为兜底策略（由 Registry 保证顺序）；提取 `title`；正文用 `body`；删 `script`/`iframe`；重建与 T009 类似但 class 可使用 `paperize-generic`。

**验收标准**

- 最小普通 HTML 转标准 Paperize 文档不崩溃。
- pytest 基本用例。

**依赖**：T004（可与 T005–T009 并行开发，但合并前需 T004）；**建议**在 T009 之后联调以复用骨架逻辑。

---

### T011 — 实现 `CleanerRegistry` / `choose_cleaner`

**内容**

在 `src/paperize/cleaner/__init__.py`（或 `registry.py`，与 `plan.md` 一致即可）提供 `choose_cleaner(html: str) -> BaseCleaner`：优先 `SimpreadCleaner`，否则 `GenericCleaner`。

**验收标准**

- 简悦样例走 `SimpreadCleaner`；普通 HTML 走 `GenericCleaner`。
- pytest 覆盖两种 HTML。

**依赖**：T005、T010。

---

## Phase 4：样式与运行时补丁

**目标**：打印 CSS 与 JS 可被 Renderer 加载。

### T012 [P] — `assets/styles/paperize-base.css`

**内容**

A4 基础打印：`@page` A4、默认 margin 14mm、`body` 字体与版心、`h1`/`p`、`img` max-width、`pre` 换行、`table`/`blockquote` 打印友好规则。

**验收标准**

- 文件存在且非空；含 `@page`、`img`、`pre`、`table`、`blockquote` 相关规则。

**依赖**：T002。

---

### T013 [P] — `assets/styles/simpread-a4.css`

**内容**

针对简悦自定义标签：`sr-read`、`sr-rd-content`、`sr-rd-mult`、`sr-rd-mult-content` 等 `display`/`flow` 重置；`sr-rd-mult-avatar` 与目录/控制栏/反馈层等 `display: none`（与 spec 列表及 `example_html` 对照）；`sr-rd-desc` 可隐藏。

**验收标准**

- 文件存在；含对 `sr-rd-mult`、`sr-rd-mult-avatar`、`sr-rd-content` 的明确规则。

**依赖**：T002（可与 T012 并行）。

---

### T014 — `runtime_patch.js`

**内容**

懒加载图：`img[data-src]` / `img[data-original]` → `src`；删空 `p`；给过宽 `table` 加 class 标记；保持轻量（复杂 DOM 仍在 Python）。

**验收标准**

- 文件存在；可被 Playwright `add_script_tag` 或等价方式注入执行。
- 不包含主流程清洗大逻辑。

**依赖**：T002。

---

## Phase 5：渲染、文件安全、单文件服务与 CLI（MVP 主路径）

**目标**：`paperize input.html -o output.pdf` 端到端可用。

### T015 — `Renderer` 单文件 PDF 导出（`renderer.py`）

**内容**

函数如 `render_pdf(cleaned_html_path: Path, output_pdf_path: Path, options: ConvertOptions, css_paths: list[Path])`：

1. 启动 Playwright Chromium；2. `page.goto(cleaned_html_path.as_uri())`；3. `emulated_media` = print；4. 注入 CSS；5. 注入 `runtime_patch.js`；6. 等待图片加载；7. `page.pdf(...)`：`format=A4`，`margin` 来自 options，`print_background`、`prefer_css_page_size` 与 research 一致。

**验收标准**

- 对已知 `cleaned.html` 可生成 PDF；失败抛明确异常（供上层转中文）。
- 支持 margin、`print_background`。

**依赖**：T012、T014；建议 T013 在简悦路径一并注入。

---

### T016 — 文件名安全化 `safe_filename`

**内容**

实现 `safe_filename(title: str) -> str`：保留中文；移除 Windows 非法字符；最大长度截断；空 → `untitled`；去尾部空格与点。

**验收标准**

- `tests/test_filename.py` 覆盖非法字符、中文、空串、尾部 `.`。

**依赖**：T003（可选无）。

---

### T017 — 单文件转换服务 `convert_one`

**内容**

流程：读源 HTML → `choose_cleaner` → `clean` → 写临时 `cleaned.html`（`debug` 时复制到 `.paperize-debug/<slug>/`）→ 调 `render_pdf` → 组装 `ConvertResult`。`output_path` 存在且非 `overwrite` 时拒绝（中文消息）。

**验收标准**

- 单 HTML 可生成 PDF（与 T015 联调）。
- 覆盖/拒绝逻辑与 debug 落盘符合 spec/research。
- 错误路径返回中文 `message`，不泄露大段原文。

**依赖**：T011、T015、T016；T003。

---

### T018 — CLI 单文件命令（`cli.py`）

**内容**

`paperize INPUT -o OUTPUT.pdf`：中文进度/成功路径提示；失败中文原因；`--debug`、`--overwrite`；默认非 debug **不**向用户打印完整 Python traceback（可选 `--verbose` 后续扩展）。

**验收标准**

- `uv run paperize <fixture>.html -o /tmp/out.pdf` 可用（fixture 可小）。
- `--help` 中文可读。

**依赖**：T017、T001。

---

## Phase 6：批量、目录扫描、debug 汇总

**目标**：目录递归、独立失败、中文汇总；debug 产物齐全。

### T019 — 目录扫描

**内容**

输入为目录时：收集 `.html`/`.htm`；`--recursive` 控制是否递归；无文件时中文提示。

**验收标准**

- 非递归仅当前目录；递归包含子目录。
- 0 个 HTML 时有明确中文提示。

**依赖**：T018。

---

### T020 — 批量转换

**内容**

`paperize ./input_dir --out ./output_dir --recursive`：每文件独立 try/except；失败不中断整体；结束输出总数/成功/失败/输出目录；命名：`safe_filename(title)` 优先否则 stem；冲突后缀；已存在 PDF 默认跳过或失败并提示 `--overwrite`（与 spec 一致）。

**验收标准**

- 多文件目录实测可跑通；失败列表中文可见。

**依赖**：T019、T016。

---

### T021 — debug 输出目录

**内容**

`--debug` 时每个任务（或每个源文件）写入 `.paperize-debug/<slug>/`：`original.html`、`cleaned.html`、拷贝 `paperize-base.css`、本次使用的 `simpread-a4.css` 或 `generic-a4.css`、`render.log`（关键步骤时间戳/阶段名）；CLI 打印 debug 目录绝对路径。

**验收标准**

- 用户可打开 `cleaned.html` 目视；`render.log` 含关键步骤。

**依赖**：T017；与 T020 可同时收尾。

---

## Phase 7：文档、测试加固、开发命令

**目标**：新用户按 README 跑通；pytest 全绿；Docker 仅文字预留。

### T022 — README（中文）

**内容**

包含：Paperize 是什么、解决什么问题、`uv` 安装、`playwright install chromium`、单文件/批量示例、`--debug` 说明、当前限制；**不**承诺 Web UI/Docker 已实现。

**验收标准**

- 新克隆仓库用户仅依 README 可完成 MVP 命令（与 `quickstart.md` 可互补，避免矛盾）。

**依赖**：T018、T020、T021。

---

### T023 — 基础测试补强

**内容**

至少覆盖：`SimpreadCleaner.match`、标题提取、DOM cleanup、`safe_filename`、`GenericCleaner`、`choose_cleaner`；关键路径可在 `tests/fixtures/` 使用裁剪 HTML。

**验收标准**

- `uv run pytest` 全部通过。

**依赖**：T011、T016 及前述 Cleaner 任务。

---

### T024 — README 开发命令说明

**内容**

在 README 中增加：`uv sync`、`uv run playwright install chromium`、`uv run paperize --help`、`uv run pytest`；可选一句「后续 Docker：见 plan/research 预留方向」。

**验收标准**

- 开发者可复制粘贴执行；表述清晰。

**依赖**：T022。

---

## 依赖关系总览（简图）

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T011
                              ↘ T010 ────────────────┘
T002 → T012, T013, T014
T012,T013,T014,T016,T011 → T015 → T017 → T018 → T019 → T020 → T021
T018,T020,T021 → T022 → T024
T023 贯穿 Cleaner/文件名阶段，建议在 T011 后集中补全至绿。
```

## MVP 完成检查点

- [ ] `uv run paperize example_html/某.html -o /tmp/x.pdf`（或 `tests/fixtures`）成功。
- [ ] `uv run paperize ./某目录 --out ./pdf --recursive` 成功且中文汇总。
- [ ] `--debug` 产物齐全；`uv run pytest` 通过；README 中文可用。

## Parallel 机会

- **T012 ∥ T013 ∥ T014**（样式与 JS）。
- **T016** 可与 Phase 3 中后期并行。
- **T010** 在 T004 完成后可与 T005–T008 并行，建议与 T009 前合并联调。

---

**说明**：本文件对应用户请求的 24 项任务清单，并与 `spec.md` / `plan.md` 对齐；实现顺序可按 Phase 微调，但**勿**在未完成 T017 前宣称 MVP 完成。
