# Feature Specification: Paperize MVP（简悦离线 HTML → A4 PDF）

**Feature Branch**: `001-paperize-mvp`

**Created**: 2026-05-14

**Status**: Draft

**Input**: 产品需求规格说明：本地将 Simpread / 简悦离线 HTML 转为 A4 打印友好 PDF；中文 CLI；批量与 debug；隐私离线。

## 概述

**一句话**：Paperize 是一个将 Simpread / 简悦离线 HTML 文章转换为 A4 打印友好 PDF 的本地工具。

**用户画像**：拥有大量离线 HTML 文章存档的个人用户；使用简悦保存文章，浏览器阅读体验好，但 Chrome 默认打印或惠普 A4 打印排版差，需要本地工具批量转换为更适合阅读、归档、打印的 PDF。

**产品目标**

1. 将简悦离线 HTML 转为 A4 友好 PDF。
2. 保留文章主体内容。
3. 去除不适合打印的阅读器 UI。
4. 正文宽度、字体、行距、页边距适合打印。
5. 支持单文件与目录批量转换。
6. 支持中文 CLI 与 debug 排查。
7. 架构上为后续 Windows 与 Docker 预留空间。

**非目标（第一版）**

1. 不做 Web UI。
2. 不做云服务。
3. 不追求完美还原网页样式。
4. 不支持所有 HTML 站点的复杂适配。
5. 不做 OCR。
6. 不做在线文章抓取。
7. 不上传任何用户文件。

**核心问题（Chrome 默认打印简悦离线 HTML 时常见）**

1. 页面宽度不适合 A4。
2. 字体大小不适合打印。
3. 标题、摘要、正文块重复。
4. 阅读器 UI 进入打印结果。
5. 卡片布局、头像栏、摘要栏导致分页异常。
6. 逐字竖排、窄列排版。
7. 图片、表格、代码块分页不友好。
8. PDF 页数膨胀、阅读体验差。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 单个 HTML 转 PDF（Priority: P1）

作为用户，我希望执行 `paperize article.html -o article.pdf`，得到 A4 打印友好的 PDF。

**Why this priority**：单文件转换是 MVP 最小闭环，验证清洗、渲染、样式全链路。

**Independent Test**：准备一份典型简悦 `article.html`，执行单文件命令，检查输出 PDF 存在且可打开。

**Acceptance Scenarios**:

1. **Given** 输入 HTML 文件存在且可读，**When** 用户执行 `paperize article.html -o article.pdf`，**Then** 在指定路径生成 PDF 文件。
2. **Given** 成功转换，**When** 用户打开 PDF，**Then** 默认纸张为 A4，页边距适合常见家用/办公打印。
3. **Given** 输入为简悦 HTML，**When** 用户查看 PDF，**Then** 不应出现简悦浮动目录、控制栏、阅读进度条等屏幕阅读 UI。
4. **Given** 转换失败（如文件不存在、渲染失败），**When** 程序退出，**Then** 终端显示中文错误提示，且非 debug 模式下日志不包含大段原文。

---

### User Story 2 - 批量转换目录（Priority: P2）

作为用户，我希望执行 `paperize ./simpread-backup --out ./pdf --recursive`，批量将目录下 HTML 转为 PDF。

**Why this priority**：批量是核心用户场景，但在单文件打通后可独立交付。

**Independent Test**：构造含多个 `.html`/`.htm` 的目录树，执行递归命令，核对输出 PDF 数量与命名。

**Acceptance Scenarios**:

1. **Given** 目录中存在 `.html` 与 `.htm` 文件（含子目录），**When** 用户使用 `--recursive`，**Then** 递归发现并处理这些文件。
2. **Given** 每个输入 HTML，**When** 转换成功，**Then** 生成一一对应的 PDF（路径与命名规则在实现中定义，文件名基于 HTML 标题或原始文件名）。
3. **Given** 标题或文件名含中文或特殊字符，**When** 生成输出名，**Then** 文件名经过安全化处理，在 macOS/Windows 合法可用。
4. **Given** 目标 PDF 已存在且用户未传 `--overwrite`，**When** 转换该条目，**Then** 默认跳过或失败并中文提示，不静默覆盖。
5. **Given** 用户传入 `--overwrite`，**When** 目标 PDF 已存在，**Then** 允许覆盖写入。

---

### User Story 3 - Simpread HTML 自动识别与清洗（Priority: P1）

作为用户，我希望 Paperize 识别简悦离线 HTML 并应用专门清洗规则，再进入打印渲染。

**Why this priority**：产品定位以简悦备份为主，专用清洗是差异化核心。

**Independent Test**：使用含 `sr-rd-content` 等特征的 fixture，运行清洗与转换，断言 DOM 与输出行为符合下列规则。

**Acceptance Scenarios**:

1. **Given** HTML 中出现简悦相关特征（如 `simpread`、`sr-rd-content`、`sr-read` 等），**When** 选择 Cleaner，**Then** 系统 MUST 识别为 Simpread HTML 并选用 `SimpreadCleaner`。
2. **Given** 识别为简悦文档，**When** 提取元数据，**Then** 优先使用 `sr-rd-title` 作为标题来源（用于显示或文件命名，以实现为准）。
3. **Given** 识别为简悦文档，**When** 提取正文，**Then** 优先以 `sr-rd-content` 作为正文主体区域。
4. **Given** 文档中含不适合打印的节点（如 `sr-rd-mult-avatar`、目录相关 `toc`/`toc-bg`、`read-process`、`sr-rd-crlbar` 等），**When** 清洗完成，**Then** 这些元素 MUST 从用于打印的 DOM 中移除或等价处理。
5. **Given** 清洗完成，**When** 进入渲染，**Then** 输入为结构标准化的文档（实现中可物化为内部 `cleaned.html` 或等价内存表示；debug 模式下 MUST 可落盘为 `cleaned.html`）。

---

### User Story 4 - A4 打印样式（Priority: P1）

作为用户，我希望输出 PDF 的正文版式适合 A4 打印与阅读。

**Why this priority**：版式是产品承诺的直接体现，与 US1 共同构成「可用 PDF」。

**Independent Test**：对同一份 fixture 生成 PDF，检查打印 CSS 约定（可通过导出 debug 中的 CSS 与人工目视 PDF 结合）。

**Acceptance Scenarios**:

1. **Given** 使用默认配置，**When** 生成 PDF，**Then** `@page` 尺寸为 A4。
2. **Given** 默认页边距，**When** 测量或审查 CSS，**Then** 页边距约在 12mm–16mm 区间（具体值以实现为准，须文档化）。
3. **Given** 正文排版，**When** 审查样式，**Then** 正文字号约在 10.5pt–11pt 区间。
4. **Given** 中文正文，**When** 渲染，**Then** 字体栈优先使用系统中文字体（如 macOS PingFang SC、Windows Microsoft YaHei），缺失时合理回退。
5. **Given** 正文段落，**When** 审查样式，**Then** 行高建议在 1.55–1.75 区间。
6. **Given** 文档含图片，**When** 打印布局，**Then** 图片最大宽度不超过正文区域。
7. **Given** 文档含表格，**When** 打印布局，**Then** 表格不应轻易撑爆页面（允许折行、缩小字体或横向策略，以实现为准）。
8. **Given** 文档含代码块，**When** 打印布局，**Then** 代码块应自动换行或安全缩放以避免溢出。
9. **Given** 引用块、代码块、图片，**When** 分页，**Then** 尽量避免在元素中部断开（使用 `break-inside` 等策略；极端长内容允许合理截断并文档化限制）。

---

### User Story 5 - Debug 模式（Priority: P2）

作为用户，我希望在版式异常时查看中间产物，例如执行 `paperize article.html -o article.pdf --debug`。

**Why this priority**：提升可维护性与用户自助排查能力，不阻塞首版主路径。

**Independent Test**：带 `--debug` 运行，检查 debug 目录内容与 CLI 是否打印路径。

**Acceptance Scenarios**:

1. **Given** 用户传入 `--debug`，**When** 转换结束（成功或失败以实现约定为准），**Then** 在约定位置生成 debug 目录。
2. **Given** debug 目录已生成，**When** 用户列出文件，**Then** 至少包含：`original.html`、`cleaned.html`、注入的 Paperize 打印 CSS（文件名以实现为准，规格要求「paperize css」可检索）、`render.log`。
3. **Given** debug 模式，**When** CLI 结束，**Then** 终端以中文提示 debug 目录路径。
4. **Given** `cleaned.html`，**When** 用户用浏览器打开，**Then** 可直观检查清洗后结构（样式以实现为准）。

---

### User Story 6 - 中文交互（Priority: P1，横切）

作为用户，我希望命令行提示、日志与汇总为中文，参数名可为英文。

**Why this priority**：目标用户为中文环境，可读性与信任度依赖语言一致性。

**Independent Test**：运行 `--help`、成功与失败路径、批量汇总，人工或快照断言中文文案。

**Acceptance Scenarios**:

1. **Given** 用户执行 `--help`，**When** 阅读输出，**Then** 说明尽量为中文（选项名可为英文，如 `--out`、`--recursive`、`--debug`）。
2. **Given** 转换过程，**When** 输出进度或状态日志，**Then** 使用中文描述（如「正在清洗 HTML」「正在生成 PDF」类语义）。
3. **Given** 任意可恢复错误，**When** 程序提示，**Then** 错误信息为中文。
4. **Given** 批量转换完成，**When** CLI 输出汇总，**Then** 成功/失败数量与失败原因摘要为中文。

---

### Edge Cases

- 输入路径不存在、无读权限或不是 `.html`/`.htm`/目录时，如何中文提示并退出码约定？
- HTML 无简悦特征时：是否回退 `GenericCleaner`，以及正文提取失败时的中文错误（如「未找到正文区域」）。
- `sr-rd-content` 存在但为空、或被脚本动态填充：超时/等待策略与失败提示。
- Playwright Chromium 未安装或损坏：中文引导安装命令（如 `playwright install chromium`），不依赖系统 Chrome。
- 磁盘空间不足、输出目录不可写：中文错误且不损坏原始 HTML。
- 单文件模式下 `-o` 与目录模式下 `--out` 冲突或缺失：参数校验与中文说明。
- 极大文件或极深目录：首版允许串行与较长耗时，但 MUST 有进度或计数反馈，避免静默挂死。

## Requirements *(mandatory)*

### Functional Requirements

**CLI**

- **FR-001**：系统 MUST 提供入口 `paperize INPUT`，其中 `INPUT` 为单文件（`.html`/`.htm`）或目录路径。
- **FR-002**：系统 MUST 支持 `paperize INPUT -o OUTPUT` 指定单输出 PDF 路径。
- **FR-003**：系统 MUST 支持 `paperize INPUT --out OUTPUT_DIR` 指定批量输出目录。
- **FR-004**：系统 MUST 支持 `paperize INPUT --recursive` 递归处理子目录中的 HTML。
- **FR-005**：系统 MUST 支持 `paperize INPUT --paper A4`（默认 A4；其他纸张可预留，第一版以实现为准）。
- **FR-006**：系统 MUST 支持 `paperize INPUT --margin 14mm`（或等价语法），用于覆盖默认页边距。
- **FR-007**：系统 MUST 支持 `paperize INPUT --debug`，生成调试产物目录。
- **FR-008**：系统 MUST 支持 `paperize INPUT --overwrite`，显式允许覆盖已存在 PDF。

**输入 / 输出**

- **FR-009**：输入 MUST 支持单个 `.html`、`.htm`、目录；目录配合 `--recursive` 时递归扫描。
- **FR-010**：输出 MUST 支持单 PDF、批量多 PDF；debug 模式下 MUST 支持中间 HTML 与 CSS、日志落盘。

**Cleaner 架构**

- **FR-011**：系统 MUST 提供 `BaseCleaner` 抽象（或协议），含适用性判断与清洗接口（如 `match()` / `clean()`，以实现为准）。
- **FR-012**：系统 MUST 提供 `SimpreadCleaner`，满足 US3 验收。
- **FR-013**：系统 MUST 提供 `GenericCleaner`，用于非简悦 HTML 的尽力而为清洗（允许能力弱于简悦路径）。

**Renderer**

- **FR-014**：渲染 MUST 使用 Playwright 驱动的 Chromium，且使用项目管理的浏览器二进制，不依赖用户系统 Chrome。
- **FR-015**：PDF 导出 MUST 使用打印（print）媒体与 A4 版式；`print_background` 行为须有默认值并可在配置或参数中覆盖（默认以实现为准，须与「背景简洁」宪法一致）。
- **FR-016**：渲染前 MUST 等待图片加载完成（含懒加载修补策略）；可实现少量 JS runtime patch（独立脚本如 `runtime_patch.js` 或等价）。
- **FR-017**：系统 MUST 支持向页面注入 Paperize 打印 CSS。

**样式资产**

- **FR-018**：样式 MUST 以独立 CSS 文件维护，至少包含：`paperize-base.css`、`simpread-a4.css`、`generic-a4.css`（路径建议 `src/paperize/assets/styles/`，与宪法一致）。

**日志**

- **FR-019**：单文件转换时，CLI MUST 显示该文件转换状态（成功/失败）。
- **FR-020**：批量转换时，CLI MUST 显示成功/失败数量；对失败项给出原因摘要（中文）。
- **FR-021**：`--debug` 时，CLI MUST 提示中间产物路径。

### Key Entities

- **SourceHtml**：用户提供的只读离线 HTML 文件路径与内容句柄。
- **CleanedDocument**：清洗后的 DOM / 内存文档；debug 下可序列化为 `cleaned.html`。
- **StyleBundle**：基础与来源专用（简悦/通用）打印样式集合。
- **RenderJob**：浏览器页面临时 URL、视口、PDF 选项、注入 CSS/JS 的封装。
- **PdfOutput**：输出 PDF 路径；受「不默认覆盖」与文件名安全规则约束。
- **DebugBundle**：`original.html`、`cleaned.html`、注入 CSS 副本、`render.log` 及目录根路径。

### Non-Functional Requirements

**隐私与安全**

- **NFR-001**：所有转换 MUST 在本地进程内完成；不上传用户 HTML/PDF。
- **NFR-002**：默认 MUST NOT 发起网络请求拉取文章资源。
- **NFR-003**：日志 MUST NOT 默认输出大段用户文档原文（与宪法一致）。

**性能**

- **NFR-004**：单文件转换耗时首版以「可接受」为目标，不定义严格 SLA；批量首版允许串行。

**可维护性**

- **NFR-005**：模块 MUST 分层：`cli`、`config`、`cleaner`、`renderer`、样式资产相互解耦；渲染逻辑集中在 `renderer`。
- **NFR-006**：每个 Cleaner SHOULD 可单独通过 pytest 测试；CSS 独立文件维护。

**可测试性**

- **NFR-007**：pytest MUST 覆盖 `SimpreadCleaner` 的关键行为：特征识别、标题提取、噪声节点移除、`cleaned` 结构属性（具体断言以实现为准）。
- **NFR-008**：应有 fixture（如 `tests/fixtures/simpread_sample.html`）支撑回归。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**：新克隆仓库的开发者在安装说明指引下，可通过 `uv sync` 安装依赖，并在安装 Playwright Chromium 后成功运行一次单文件转换。
- **SC-002**：对提供的简悦样例 HTML，`paperize input.html -o output.pdf` 在默认参数下生成可打开的 PDF，且肉眼检查无「整段竖排碎字」、无「重复摘要块」等明显缺陷（以 fixture 基线为准迭代）。
- **SC-003**：`paperize input_dir --out output_dir --recursive` 在含多文件的目录树上，生成与输入一一对应的 PDF，且默认不覆盖已存在文件。
- **SC-004**：`--debug` 运行后，用户可在指示路径找到 `original.html`、`cleaned.html`、CSS 与 `render.log`。
- **SC-005**：`--help` 与典型错误路径下，用户可见字符串主体为中文。

### MVP 验收清单（与实现发布对齐）

1. `uv sync` 后可运行 CLI。
2. Playwright Chromium 安装后可生成 PDF。
3. `paperize input.html -o output.pdf` 可用。
4. `paperize input_dir --out output_dir --recursive` 可用。
5. 对简悦 HTML 走专用清洗路径。
6. 典型样例 PDF 无明显竖排碎字与重复摘要块。
7. debug 模式可查看 `cleaned.html`。

## Assumptions

- 用户使用 Python >= 3.11，接受通过 `uv` 管理环境与 lockfile。
- 第一版以 macOS 为主要开发与验证平台，同时代码层遵守 pathlib 与跨平台约束，为 Windows 与 Docker 预留验证任务。
- 用户理解首版不保证任意站点 HTML 完美转换，极端页面允许失败但须有中文原因与日志。
- 命令名 `paperize` 通过 `pyproject.toml` 的脚本入口或等价方式暴露（以实现为准）。

## 附录：建议仓库布局

```text
paperize/
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
│   └── paperize/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── renderer.py
│       ├── runtime_patch.js
│       ├── cleaner/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── simpread.py
│       │   └── generic.py
│       └── assets/
│           └── styles/
│               ├── paperize-base.css
│               ├── simpread-a4.css
│               └── generic-a4.css
├── tests/
│   ├── test_simpread_cleaner.py
│   ├── test_filename.py
│   └── fixtures/
│       └── simpread_sample.html
└── examples/
```

本附录为建议性结构，实现阶段若调整目录，MUST 在 `plan.md` 中记录结构决策并同步更新本规格。
