# Implementation Plan: Simpread Paperize 品牌与分发重命名

**Branch**: `002-simpread-rebrand` | **Date**: 2026-05-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-simpread-rebrand/spec.md`

**Note**: 本计划由 `/speckit-plan` 生成；实现任务见同目录 **`tasks.md`**（由 `/speckit-tasks` 生成，本命令不创建）。

## Summary

在**不改变**清洗/渲染语义的前提下，将分发标识从 `paperize` 统一为 **`simpread_paperize`**（包与 Git 仓库名）与 **`sr_paperize`**（终端命令）：`src/paperize/` → `src/simpread_paperize/`、全量 Python import 替换、`pyproject.toml` 元数据与 `[project.scripts]` 更新、README/LICENSE 与 `002` 契约文档对齐。内部 HTML/CSS 类名、样式文件名、`.paperize-debug/` 与 `tempfile` 前缀等**保持 MVP 命名**，以降低版式回归风险。

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: 与 `001-paperize-mvp` 相同 — `typer`、`rich`、`beautifulsoup4`、`lxml`、`playwright`；包管理 **uv**

**Storage**: 无变更；本地文件只读输入、PDF/debug 输出策略不变

**Testing**: `pytest`（`tests/test_filename.py`、`tests/test_simpread_cleaner.py`、`tests/test_renderer_footer.py`）；验收 grep 零残留 `from paperize` / `import paperize`

**Target Platform**: macOS / Windows 开发与使用（`pathlib`）；本特性不交付 Docker 镜像

**Project Type**: Python CLI 单包；重命名后布局 `src/simpread_paperize/`

**Performance Goals**: 无新要求；行为与 MVP 基线一致

**Constraints**: 宪法全文适用；不上 PyPI、不引入 CI 徽章流水线；不重写 Cleaner/renderer；不修改内部 `paperize-*` 标识（见下文「保持不变」）

**Scale/Scope**: 工程/分发变更；约 15 个 Python 源文件 + `pyproject.toml` + `README.md` + 3 个测试文件 + 本特性 `contracts/cli.md`

## Constitution Check

*GATE: Phase 0 前与 Phase 1 设计后均须通过。*

| 门禁 | 结论 | 说明 |
|------|------|------|
| **中文优先** | **通过** | 仅更新 CLI docstring/帮助中的**命令示例**为 `sr_paperize`；用户可见文案仍为中文。产品对外称呼在 README 使用「Simpread Paperize」/ `sr_paperize`。 |
| **可复现与离线** | **通过** | 仍使用 `uv` + `pyproject.toml` + `uv.lock`；Playwright 锁定 Chromium；无新增网络依赖。 |
| **只读源与安全输出** | **通过** | 重命名不修改 `convert.py` 覆盖策略、`--overwrite` 语义或源 HTML 只读约束。 |
| **清洗优先与分层** | **通过** | 目录迁移保持 `cleaner/`、`renderer.py`、`convert.py`、`cli.py`、`config.py`、`assets/styles/` 分层；不把逻辑合并进单文件。 |
| **扩展与跨平台** | **通过** | `CleanerRegistry` / `match`/`clean` 不变；`pathlib` 用法不变。 |
| **打印目标与 MVP** | **通过** | A4、debug、批量等行为继承 `001`；本特性不放宽或收紧产品能力边界。 |
| **规格对齐** | **通过** | 本计划可追溯至 [spec.md](./spec.md) FR-001–FR-009、US1–US3、SC-001–SC-006。 |

**Phase 1 设计后复核**：`contracts/cli.md` 仅将命令名由 `paperize` 改为 `sr_paperize`；选项表与 `001` 一致。`data-model.md` 声明无实体变更。无宪法违规需记入 Complexity Tracking。

## Project Structure

### Documentation (this feature)

```text
specs/002-simpread-rebrand/
├── plan.md              # 本文件
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── cli.md           # Phase 1：sr_paperize 契约
├── spec.md
└── tasks.md             # /speckit-tasks（后续）
```

### Source Code（重命名后目标树）

```text
pyproject.toml                 # project.name、scripts、package-data 键更新
LICENSE                        # 新增 MIT
README.md                      # 安装、命令、许可、Chromium
src/simpread_paperize/         # 自 src/paperize/ 整目录迁移
├── __init__.py
├── cli.py
├── config.py
├── convert.py
├── models.py
├── renderer.py
├── filename.py
├── runtime_patch.js
├── cleaner/
│   ├── __init__.py
│   ├── base.py
│   ├── simpread.py
│   └── generic.py
└── assets/styles/
    ├── paperize-base.css      # 文件名不变
    ├── simpread-a4.css
    └── generic-a4.css
tests/
├── test_filename.py
├── test_simpread_cleaner.py   # 断言 paperize-* class 仍保留
└── test_renderer_footer.py
```

**Structure Decision**: 单包 `src/simpread_paperize`；删除空目录 `src/paperize/` 及陈旧 `src/paperize.egg-info/`（若存在则 `uv sync` 再生）。**不修改** `specs/001-paperize-mvp/` 内历史文档（见「与 001 关系」）。

## 实施策略

### 1. 文件 / 目录迁移清单

| 动作 | 路径 | 说明 |
|------|------|------|
| **重命名目录** | `src/paperize/` → `src/simpread_paperize/` | `git mv` 或等价，保留 `assets/` 子树 |
| **删除旧包根** | `src/paperize/` | 迁移并验证 import 后删除 |
| **更新元数据** | `pyproject.toml` | `project.name = "simpread_paperize"`；`[project.scripts] sr_paperize = "simpread_paperize.cli:app"`；**移除** `paperize` script；`[tool.setuptools.package-data] simpread_paperize = [...]` |
| **同步锁文件** | `uv.lock` | `uv lock` 或 `uv sync` 后提交 |
| **Python 源文件** | `src/simpread_paperize/**/*.py` | 所有 `from paperize` → `from simpread_paperize` |
| **CLI 文案** | `cli.py` | docstring/帮助示例：`paperize` → `sr_paperize`；模块 doc 可写「Simpread Paperize」 |
| **配置注释** | `config.py` | 注释中 `site-packages/paperize/` → `site-packages/simpread_paperize/`（仅注释） |
| **测试** | `tests/test_*.py` | import 路径改为 `simpread_paperize`；**保留**对 `paperize-title` 等 class 的断言 |
| **文档** | `README.md` | 克隆目录 `simpread_paperize`、`uv run` / `uv tool install`、MIT、`playwright install chromium` |
| **许可** | `LICENSE` | 新增标准 MIT 全文 |
| **契约** | `specs/002-simpread-rebrand/contracts/cli.md` | 命令 `sr_paperize`；行为对齐 `001` contracts |
| **不修改（默认）** | `specs/001-paperize-mvp/**` | 历史 spec/plan/tasks 保留 `paperize` 叙述 |

可选 follow-up（**不在本特性 tasks 内**，除非维护者单独开项）：

- 在 `001` 的 `quickstart.md` / `contracts/cli.md` 顶部加一行「已废弃：请见 `002`」——**非阻塞**。

### 2. 批量替换策略（避免半迁移）

按**严格顺序**执行，任一阶段失败则停止，不提交半成品：

1. **冻结行为基线**：在重命名前于当前分支执行 `uv run pytest` 并记录全绿（可选：对 fixture 跑一次 `uv run paperize` smoke 备查）。
2. **目录级迁移**：`git mv src/paperize src/simpread_paperize`（一次性移动全部子文件，含 `assets/` 与 `runtime_patch.js`）。
3. **包内 import 批量替换**（仅 `src/simpread_paperize/**/*.py`）：
   - `from paperize.` → `from simpread_paperize.`
   - `import paperize` → `import simpread_paperize`（若存在）
4. **更新 `pyproject.toml`** 并执行 `uv sync`（确保 entry point 与 package-data 指向新包名）。
5. **测试目录替换**：`tests/**/*.py` 中 import 同上。
6. **CLI 用户可见字符串**：`cli.py` 内帮助示例与 `main` 文档字符串中的命令名。
7. **README / LICENSE / 002 文档**。
8. **全仓验收 grep**（排除 `specs/001-*`、`.paperize-debug`、`paperize-base.css`、CSS/HTML class 字面量）：
   ```bash
   # 应无匹配（示例，实现时可用 ripgrep）
   rg 'from paperize|import paperize' --glob '*.py'
   rg 'paperize\.cli:app' pyproject.toml
   ```
9. **删除** `src/paperize/`（若残留）及过时 `*.egg-info`。

**禁止**：在 `src/paperize` 仍存在时只改 `pyproject` 或只改部分文件的 import（会导致 `uv run` 与测试处于半迁移状态）。

### 3. 「保持不变」清单（勿改）

| 类别 | 标识 / 路径 | 位置示例 |
|------|-------------|----------|
| 调试目录名 | `.paperize-debug/` | `convert.py` |
| 临时目录前缀 | `tempfile.TemporaryDirectory(prefix="paperize-")` | `convert.py` |
| CSS 文件名 | `paperize-base.css` | `convert.py` 中 `styles_dir() / "paperize-base.css"` |
| 样式链 | `simpread-a4.css`、`generic-a4.css` 加载顺序 | `convert.py` |
| HTML/CSS class | `paperize-document`、`paperize-title`、`paperize-content`、`paperize-mult-author`、`paperize-table-wide`、`paperize-simpread`、`paperize-generic` | `simpread.py`、`generic.py`、`*.css`、`runtime_patch.js` |
| 内部包装 id | `paperize-inner` | `simpread.py` |
| JS 运行时 | `paperize-table-wide` class 注入 | `runtime_patch.js` |
| 测试断言 | 输出 HTML 含 `paperize-title` 等 | `test_simpread_cleaner.py` |

> **说明**：上述保留是为**版式与清洗行为零回归**；与对外品牌 `simpread_paperize` / `sr_paperize` 正交。

### 4. 验证计划

| 步骤 | 命令 | 通过标准 |
|------|------|----------|
| 1 | `uv sync` | 无解析错误；依赖安装完成 |
| 2 | `uv run sr_paperize --help` | 退出码 0；帮助为中文；示例命令为 `sr_paperize` |
| 3 | `uv run pytest` | 全部通过 |
| 4 | `rg 'from paperize\|import paperize' -g '*.py'` | 零匹配（全仓含 tests） |
| 5 | `rg '^\s*paperize\s*=' pyproject.toml` 或检查 `[project.scripts]` | 仅 `sr_paperize` 条目 |
| 6（可选 smoke） | `uv tool install -e .` 后 `sr_paperize <fixture> -o /tmp/out.pdf` | PDF 可打开；与 MVP smoke 同级 |
| 7（可选 Git 安装） | `uv tool install "simpread_paperize @ git+https://github.com/<owner>/simpread_paperize.git"` | PATH 中 `sr_paperize --help` 可用 |

Playwright：若环境未装浏览器，先 `uv run playwright install chromium`（与 README 一致）。

### 5. 与 `001-paperize-mvp` 的关系

| 项 | 策略 |
|----|------|
| 功能行为 | **基线**为 `001` spec 已交付能力；`002` 不得回归单文件/批量/`--debug`/`--overwrite` |
| `specs/001-paperize-mvp/` | **不修改**其中 `spec.md`、`plan.md`、`tasks.md`、`research.md` 等历史工件（保留 `paperize` 命令叙述作为 MVP 档案） |
| 契约权威 | 用户面向 CLI 契约以 **`specs/002-simpread-rebrand/contracts/cli.md`** 为准；`001/contracts/cli.md` 视为历史参考 |
| 交叉引用 | README / `002/quickstart.md` 指向新命令；可选 follow-up 在 `001` 文档加废弃注记 — **非本特性必须** |
| 宪法 | 不重命名宪法文件；`constitution.md` 中示例命令 `paperize` 可保留或后续 PATCH 统一 — **非阻塞** |

## Complexity Tracking

> 无宪法门禁违规。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Phase 0 / Phase 1 产出索引

- [research.md](./research.md) — 命令名、内部标识保留、uv tool install 模板
- [data-model.md](./data-model.md) — 无数据模型变更说明
- [contracts/cli.md](./contracts/cli.md) — `sr_paperize` 接口契约
- [quickstart.md](./quickstart.md) — 开发机与 `uv tool install` 双路径

## 明确排除（本 plan）

- Docker 镜像与容器化文档
- PyPI 发布流水线、版本徽章、GitHub Actions CI
- 内部 CSS/HTML/debug 目录重命名
- Cleaner / renderer / Playwright 逻辑重写
