# Implementation Plan: Paperize MVP（简悦离线 HTML → A4 PDF）

**Branch**: `001-paperize-mvp` | **Date**: 2026-05-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-paperize-mvp/spec.md`

**Note**: 本计划由 `/speckit-plan` 生成；任务拆解见后续 `/speckit-tasks` 产出的 `tasks.md`（本命令不生成）。

## Summary

Paperize 在本地将简悦（Simpread）等离线 HTML 经 **DOM 清洗 → 标准化 HTML → 注入打印 CSS → Playwright Chromium 打印为 PDF**。MVP 交付单文件与目录批量转换、简悦专用 `SimpreadCleaner`、通用回退 `GenericCleaner`、`CleanerRegistry` 调度、中文 CLI 与日志、`--debug` 中间产物，以及可复现的 **uv + Playwright 自带 Chromium** 管线。实现按阶段推进：项目脚手架 → Cleaner → CSS → Renderer → 单文件 CLI → 批量与汇总 → 测试与示例 → Docker 仅预留结构说明。

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: `typer`（CLI）、`beautifulsoup4` + `lxml`（解析与清洗）、`playwright`（Chromium 渲染与 `page.pdf()`）、`rich`（终端输出与可读日志）

**Storage**: 本地文件系统；原始 HTML 只读；中间 `cleaned.html` 写入临时目录或 debug 目录；PDF 写入用户指定路径；debug 下复制注入的 CSS 副本到 `.paperize-debug/<safe-slug>/`

**Testing**: `pytest`；Cleaner 与文件名安全化单元测试为主；CLI smoke test（可选 subprocess）

**Target Platform**: 首版以 macOS 开发与验证为主；代码层 MUST 使用 `pathlib`，为 Windows 与后续 Docker 预留验证

**Project Type**: Python CLI 包（`src/paperize/` 布局）

**Performance Goals**: 首版无严格 SLA；批量默认**串行**转换，单任务失败不中断整体（记录失败原因）

**Constraints**: 离线默认、不依赖系统 Chrome、不默认联网、不静默覆盖已有 PDF、日志不大段输出用户正文（见宪法）

**Scale/Scope**: 个人本地批量；单仓库 MVP；不追求全互联网 HTML 兼容

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 门禁 | 结论 | 说明 |
|------|------|------|
| 中文优先 | **通过** | CLI、`--help`、进度与错误、批量汇总均为中文；选项名保留英文。 |
| 可复现与离线 | **通过** | `uv` + `pyproject.toml` + `uv.lock`；Playwright 使用项目安装 Chromium；无默认远程拉文。 |
| 只读源与安全输出 | **通过** | 源 HTML 只读；`--overwrite` 才覆盖；输出与 debug 路径明确；PDF 文件名 `safe_filename` 处理。 |
| 清洗优先与分层 | **通过** | Cleaner 产出标准化 HTML 后再注入 CSS；样式在 `assets/styles/`；职责分 `cli` / `config` / `models` / `cleaner/` / `renderer.py` / JS / CSS。 |
| 扩展与跨平台 | **通过** | `CleanerRegistry` + `match`/`clean`；`Path.as_uri()` 打开本地页；路径一律 `pathlib`。 |
| 打印目标与 MVP | **通过** | 默认 A4、可配置 margin；极端页允许失败 + 中文原因；无 Web 服务。 |
| 规格对齐 | **通过** | 本计划与 [spec.md](./spec.md) 中 US1–US6、FR/NFR、MVP 清单一致；数据模型与 CLI 合同见同目录 `data-model.md`、`contracts/`。 |

**Phase 1 设计后复核**：`print_background` 默认值与「背景简洁」关系已在 [research.md](./research.md) 固化为「默认 `true` 以保留代码高亮可行性，实际灰底由 CSS 抑制」；若后续改为默认 `false`，须经 spec 小修订。

## Project Structure

### Documentation (this feature)

```text
specs/001-paperize-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
├── spec.md
└── tasks.md              # /speckit-tasks 生成
```

### Source Code (repository root)

```text
pyproject.toml
uv.lock
README.md
src/paperize/
├── __init__.py
├── cli.py                 # Typer：参数、中文帮助、调度
├── config.py              # 默认值、常量、环境相关路径策略
├── models.py              # ConvertOptions, CleanResult, ConvertResult
├── renderer.py            # Playwright 生命周期、注入 CSS/JS、page.pdf
├── runtime_patch.js       # 懒加载图、空段落、图片等待、宽表标记
├── registry.py            # CleanerRegistry：按序 match 选 cleaner
├── cleaner/
│   ├── __init__.py
│   ├── base.py            # BaseCleaner 抽象
│   ├── simpread.py
│   └── generic.py
└── assets/
    └── styles/
        ├── paperize-base.css
        ├── simpread-a4.css
        └── generic-a4.css
tests/
├── test_simpread_cleaner.py
├── test_filename.py
├── test_cli_smoke.py      # 可选
└── fixtures/
    └── simpread_sample.html
examples/
```

**Structure Decision**: 单包 CLI，`src/paperize` 为唯一源码根；测试与 fixture 置于仓库根 `tests/`；调试产物目录 **`.paperize-debug/<slug>/`**（相对当前工作目录或相对输出根，实现时在 `config`/`research` 中二选一并文档化，首版推荐相对**输出 PDF 所在目录**或**当前工作目录**之一，避免污染用户文档目录——以 `research.md` 决策为准）。

## Complexity Tracking

> 无宪法门禁违规需额外论证；本表留空。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
