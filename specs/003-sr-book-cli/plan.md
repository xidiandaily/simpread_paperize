# Implementation Plan: SR Book CLI（`sr_book` 成书）

**Branch**: `003-sr-book-cli` | **Date**: 2026-05-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/speckit-specify`（`specs/003-sr-book-cli/spec.md`）

**说明**：用户消息中的 `specs/NNN-sr-book/plan.md` 为编号占位；本仓库当前特性目录为 **`specs/003-sr-book-cli/`**（与分支、`setup-plan.sh` 输出一致）。

## Summary

新增与 `sr_paperize` 并列的 Typer CLI **`sr_book`**，提供 `init` / `index` / `plan` / `build` 四子命令：以 **YAML manifest** 为唯一编排源，在**不修改用户单篇 PDF** 的前提下，完成篇目磁盘编号、分页规划（表格 + JSON）、多卷合集 PDF 生成（封面 + 可打印目录 + 合并正文 + 页眉/左下角页码 + 篇级书签）。PDF 栈选型见 [research.md](./research.md)：**`pypdf` + `reportlab`**（宽松许可证、较小安装体积）。单测优先覆盖 **分卷贪心算法**、**plan 输出**、**manifest 相对路径解析**、**index 回写**。

## Technical Context

**Language/Version**: Python >= 3.11（与宪法、`pyproject.toml` 一致）

**Primary Dependencies**: `typer`、`rich`（沿用仓库 CLI 体验）；新增 **`pypdf`**（页数、合并、Outline）、**`reportlab`**（目录页 PDF / 条带型 overlay）；`PyYAML`（manifest 读写，若尚未在依赖中则新增）。**不**在成书路径引入 Playwright。

**Storage**: 本地文件系统 — `manifest.yaml`、`plan.json`、用户指定输出目录与可选 `--temp-dir`；无数据库。

**Testing**: `pytest`；优先单元测试（分卷、`plan` 结构、`paths` 解析、`index` dry-run / 回写）。

**Target Platform**: macOS / Windows（`pathlib`）；Docker 友好（仅文件 IO）。

**Project Type**: Python 包内 CLI 扩展（`simpread_paperize`）。

**Performance Goals**: 以「个人资料库规模（数十～数百 PDF）」为目标；全量 O(总页数) 读写可接受；不规定毫秒级 SLA。

**Constraints**: 全离线；日志/错误不回传正文；源单篇 PDF 只读；合集覆盖须 `--overwrite`；`plan` 不写最终合集。`build --temp-dir` 当前为**预留 CLI 参数**（合并主要在内存），与 `contracts/cli.md` / `quickstart.md` 一致；若后续写入中间文件再使用该目录。

**Scale/Scope**: 四子命令 + 共享库模块；与 `sr_paperize` 无运行时强耦合。

## Constitution Check

*GATE: Phase 0 前已通过；Phase 1 设计后复核。*

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 中文优先 | 通过 | CLI `--help`、表格列头、错误信息中文；命令/选项名可英文 |
| 可复现与离线 | 通过 | `uv` + lock；`sr_book` 不联网、不用系统 Chrome；HTML→PDF 仍由 `sr_paperize`/Playwright 负责，**与本特性正交** |
| 只读源与安全输出 | 通过 | 单篇 PDF 只读；`build` 输出新文件；`--overwrite` 控制合集覆盖；`--debug`（若加）写入明确目录且不打印正文 |
| 清洗优先与分层 | 部分 N/A + 通过 | 本特性无 HTML 清洗；**禁止**巨型单文件堆逻辑；目录样式可少量代码生成或随附资源，避免超长内嵌字符串 |
| 扩展与跨平台 | 通过 | `pathlib`；中文路径；卷/篇模型可测 |
| 打印目标与 MVP | 通过 | 目录页可打；正文版式继承单篇 PDF；失败路径中文可行动 |
| 规格对齐 | 通过 | 本 `plan.md` / 后续 `tasks.md` 追溯 [spec.md](./spec.md) FR 与验收场景 |

**N/A 说明**：宪法中「Playwright + 项目管理 Chromium」适用于 **HTML 渲染** 管线；`sr_book` **仅消费 PDF**，不触发该路径，**不视为违宪**。

## Project Structure

### Documentation (this feature)

```text
specs/003-sr-book-cli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
├── spec.md
└── tasks.md              # 由 /speckit-tasks 生成，非本命令产物
```

### Source Code（计划落点）

```text
src/simpread_paperize/
├── cli.py                  # 既有 sr_paperize，不改行为
├── book_cli.py             # 新增：Typer app，挂 init/index/plan/build
├── book/
│   ├── __init__.py
│   ├── manifest.py         # 加载/校验/写回 YAML
│   ├── paths.py            # manifest_dir 解析、禁止 path escape
│   ├── volume_plan.py      # 页数模型 + 贪心分卷 + 起始页计算（plan/build 共用）
│   ├── toc_pdf.py          # reportlab 生成目录页
│   ├── merge_build.py      # pypdf 合并、叠页眉脚、篇级书签
│   └── index_rename.py     # 数字前缀重命名 + manifest 回写
tests/
├── book/
│   ├── test_volume_plan.py
│   ├── test_manifest_paths.py
│   ├── test_index_rewrite.py
│   └── test_plan_output.py
```

**Structure Decision**: 在 `simpread_paperize` 包内新增 `book/` 子包与顶层 `book_cli.py`，避免与 `cli.py` 混杂；`pyproject.toml` 增加 `sr_book` script 与 `pypdf`、`reportlab`、`pyyaml` 依赖并由 `uv lock` 固定。

## Phase 0 / Phase 1 产出状态

| 产物 | 路径 | 状态 |
|------|------|------|
| Research | [research.md](./research.md) | 已完成（PDF 库对比与定稿） |
| Data model | [data-model.md](./data-model.md) | 已完成（manifest / plan / 算法语义） |
| CLI 契约 | [contracts/cli.md](./contracts/cli.md) | 已完成（四子命令、选项、错误码） |
| Quickstart | [quickstart.md](./quickstart.md) | 已完成 |

## Complexity Tracking

> 无宪法门禁违规需豁免。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
