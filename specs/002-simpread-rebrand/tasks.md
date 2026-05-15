---
description: "Simpread Paperize 品牌与分发重命名（/speckit-tasks 生成）"
---

# Tasks: Simpread Paperize 品牌与分发重命名（002）

> **命令约定（本特性完成后）**  
> - **日常使用**：`sr_paperize`（`uv tool install` 后位于 PATH）  
> - **开发调试**：`uv run sr_paperize`（仓库内 `uv sync` 之后）

**Input**: `specs/002-simpread-rebrand/` — `spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/`、`quickstart.md`

**约束**: 仅重命名与分发；**不**新增 Cleaner/CSS/Dockerfile；**不**修改 `specs/001-paperize-mvp/` 历史文档；内部 `paperize-*` class、`.paperize-debug/`、`paperize-base.css` **保持不变**。

**格式**: `- [X] Tnnn [P?] [USx?] …`；Setup / Foundational / Polish **无** `[USx]`；Phase 3–5 **必须** 带 `[US1]`–`[US3]`。

---

## Phase 1: Setup（元数据与许可）

**目标**: `pyproject.toml` 分发名与入口脚本就绪；MIT 许可文件就位。

**独立验收（阶段）**: `rg 'name = "simpread_paperize"' pyproject.toml` 有匹配；`rg 'sr_paperize' pyproject.toml` 有匹配；`test -f LICENSE`（Windows: `Test-Path LICENSE`）。

### Tasks

- [X] T001 更新 `pyproject.toml`：`[project].name = "simpread_paperize"`；`[project.scripts]` 仅保留 `sr_paperize = "simpread_paperize.cli:app"`，**删除** `paperize = ...` 行；验收：`rg '^\s*paperize\s*=' pyproject.toml` 在 `[project.scripts]` 段无匹配；`rg 'sr_paperize = "simpread_paperize.cli:app"' pyproject.toml` 有匹配
- [X] T002 [P] 在仓库根新增 `LICENSE`（MIT 全文，版权年份与持有人与 README 一致）；验收：`rg -i 'MIT License' LICENSE` 有匹配且文件非空

---

## Phase 2: Foundational（目录迁移与 import 基线）⚠️ 阻塞 Phase 3–5

**目标**: 包目录迁至 `src/simpread_paperize/`；Python import 与 package-data 键完成；`uv sync` 可导入新包。

**独立验收（阶段）**: `test ! -d src/paperize`（或目录不存在）；`uv run python -c "import simpread_paperize; import simpread_paperize.cleaner"` 退出码 0。

### Tasks

- [X] T003 将 `src/paperize/` **整目录**迁移为 `src/simpread_paperize/`（推荐 `git mv src/paperize src/simpread_paperize`，含 `assets/`、`runtime_patch.js`、`cleaner/`）；验收：`test -d src/simpread_paperize/cli.py` 或 `Test-Path src/simpread_paperize/cli.py`；`test ! -e src/paperize/cli.py`
- [X] T004 在 `src/simpread_paperize/**/*.py` 批量替换 import：`from paperize.` → `from simpread_paperize.`、`import paperize` → `import simpread_paperize`（**勿改** `paperize-base.css` 字符串、`paperize-document` 等 class 字面量）；验收：`rg 'from paperize|import paperize' src/simpread_paperize --glob '*.py'` 零匹配
- [X] T005 更新 `pyproject.toml` 中 `[tool.setuptools.package-data]`：键 `paperize` → `simpread_paperize`，glob 保持 `assets/styles/*.css` 与 `runtime_patch.js`；验收：`rg '^\s*simpread_paperize\s*=' pyproject.toml` 有匹配；`rg '^\s*paperize\s*=' pyproject.toml` 在 package-data 段无匹配
- [X] T006 执行 `uv sync` 并删除陈旧 `src/paperize.egg-info/`（若存在）；验收：`uv sync` 退出码 0；`uv run python -c "import simpread_paperize"` 退出码 0
- [X] T007 在 `src/simpread_paperize/config.py` 将注释中的 `site-packages/paperize/` 改为 `site-packages/simpread_paperize/`（**仅注释**）；验收：`rg 'site-packages/simpread_paperize' src/simpread_paperize/config.py` 有匹配

**Checkpoint**: Foundational 完成 — 方可进入 US1 CLI 与后续故事。

---

## Phase 3: User Story 1 — 维护者本地 `sr_paperize --help`（Priority: P1）🎯 MVP

**Story**: 见 `spec.md` US1 — `uv run sr_paperize --help` 中文帮助，示例命令为新名。

**独立测试**: `uv run sr_paperize --help` 退出码 0；输出含中文且示例为 `sr_paperize`（非推荐 `paperize`）。

### Tasks

- [X] T008 [US1] 更新 `src/simpread_paperize/cli.py`：模块/docstring 与 Typer 帮助中的示例命令 `paperize` → `sr_paperize`；产品描述可用「Simpread Paperize」；`main` 文档字符串中删除 `paperize = paperize.cli:app`，改为 `sr_paperize = simpread_paperize.cli:app`；**不修改**参数定义与 `convert_*` 调用逻辑；验收：`rg 'paperize ' src/simpread_paperize/cli.py` 在用户示例行无未标注的 `paperize` 命令（允许英文产品词 Paperize 若存在）
- [X] T009 [US1] 验证 CLI 入口：`uv run sr_paperize --help`；验收：退出码 0；`uv run sr_paperize --help 2>&1 | rg -i '单文件|批量|html|pdf'` 至少一项有匹配；帮助中 `sr_paperize` 出现且不以 `paperize` 作为**推荐**用法示例

**Checkpoint**: US1 完成 — 开发机已可用 `uv run sr_paperize`。

---

## Phase 4: User Story 2 — Git 安装路径与测试绿灯（Priority: P2）

**Story**: 见 `spec.md` US2 — 核心模块仅 import 变更；`pytest` 全绿；行为与 MVP 一致。

**独立测试**: `uv run pytest` 全部通过；`convert.py` / `renderer.py` / `cleaner/*.py` diff 无清洗或渲染逻辑改动（仅 import 与路径注释）。

### Tasks

- [X] T010 [US2] 确认 `src/simpread_paperize/convert.py` **仅** import 行相对 MVP 有变（不修改 `paperize-base.css`、`.paperize-debug/`、`prefix="paperize-"` 等业务常量）；验收：`git diff -- src/simpread_paperize/convert.py`（对比重命名前）不含 `def ` / `class ` 签名变更；`rg 'paperize-base\.css|\.paperize-debug' src/simpread_paperize/convert.py` 仍匹配
- [X] T011 [P] [US2] 确认 `src/simpread_paperize/renderer.py` 仅 import 变更；验收：`git diff` 无新增渲染/PDF 选项逻辑；`uv run python -c "from simpread_paperize.renderer import render_pdf"` 退出码 0
- [X] T012 [P] [US2] 确认 `src/simpread_paperize/cleaner/base.py`、`cleaner/simpread.py`、`cleaner/generic.py`、`cleaner/__init__.py` 仅 import 变更；**保留**输出 HTML 中 `paperize-title` 等 class；验收：`rg 'paperize-title|paperize-document' src/simpread_paperize/cleaner/simpread.py` 有匹配；`rg 'from paperize' src/simpread_paperize/cleaner --glob '*.py'` 零匹配
- [X] T013 [P] [US2] 更新 `tests/test_filename.py`、`tests/test_simpread_cleaner.py`、`tests/test_renderer_footer.py` 的 import 为 `simpread_paperize.*`；**保留** `test_simpread_cleaner.py` 中对 `paperize-title` 等 class 的断言；验收：`rg 'from paperize|import paperize' tests --glob '*.py'` 零匹配
- [X] T014 [US2] 运行全量测试：`uv run pytest`；验收：退出码 0；失败数为 0

**Checkpoint**: US2 完成 — 代码库可发布级测试通过。

---

## Phase 5: User Story 3 — README 与契约文档（Priority: P3）

**Story**: 见 `spec.md` US3 — 读者可依 README 完成克隆、`uv tool install`、Playwright、MIT。

**独立测试**: README 含四要素（仓库名、`uv run`/`uv tool install`、Chromium、MIT）；用户面向命令示例均为 `sr_paperize`。

### Tasks

- [X] T015 [US3] 重写 `README.md`：标题/定位「Simpread Paperize」；克隆目录 `simpread_paperize`；`uv sync` + `uv run sr_paperize` 示例；`uv tool install "simpread_paperize @ git+https://github.com/<owner>/simpread_paperize.git"`；`playwright install chromium` 提醒；许可证小节链接 `LICENSE`（MIT）；**用户示例命令**一律 `sr_paperize`/`uv run sr_paperize`，不出现未标注废弃的 `paperize` 推荐用法；验收：`rg 'sr_paperize' README.md` 有匹配；`rg 'uv tool install' README.md` 有匹配；`rg 'playwright install chromium' README.md` 有匹配；`rg 'MIT' README.md` 有匹配
- [X] T016 [P] [US3] 核对 `specs/002-simpread-rebrand/contracts/cli.md` 与实现一致（命令 `sr_paperize`、选项表与 `src/simpread_paperize/cli.py` 参数一致，含 `--traceback` 若已实现）；验收：`rg '^sr_paperize' specs/002-simpread-rebrand/contracts/cli.md` 有匹配；人工或 diff 确认选项名与 `cli.py` 一致
- [X] T017 [P] [US3] 同步 `specs/002-simpread-rebrand/quickstart.md` 与 `README.md` 的安装命令（`sr_paperize`、`uv tool install` 模板一致）；验收：`rg 'sr_paperize' specs/002-simpread-rebrand/quickstart.md` 有匹配；无 `uv run paperize` 残留

**Checkpoint**: US3 完成 — 对外文档与契约对齐。

---

## Final Phase: Polish（全库验收与 smoke）

**目标**: 零残留旧包 import/脚本；可选 smoke 证明 PDF 可生成。

**独立验收（阶段）**: grep 验收通过；smoke 命令生成非空 PDF。

### Tasks

- [X] T018 全库 Python import 残留检查（含 `tests/`）：`rg 'from paperize|import paperize' --glob '*.py' .`；验收：**零匹配**（允许 `specs/001-paperize-mvp/`、`paperize-base.css`、`paperize-title` 等非 import 上下文）
- [X] T019 分发入口残留检查：`rg 'paperize\.cli:app' pyproject.toml`；验收：零匹配；`rg 'sr_paperize' pyproject.toml` 有匹配
- [X] T020 [P] 对照 `specs/002-simpread-rebrand/plan.md`「保持不变」清单 spot-check：`rg '\.paperize-debug|paperize-base\.css|paperize-document' src/simpread_paperize`；验收：均有匹配（证明未误删内部标识）
- [X] T021 smoke：对已安装 Chromium 的环境执行 `uv run sr_paperize tests/fixtures/simpread_min.html -o /tmp/sr_paperize_smoke.pdf`（Windows 可用 `$env:TEMP\sr_paperize_smoke.pdf`）；验收：退出码 0；输出 PDF 存在且大小 > 0
- [ ] T022（可选）`uv tool install -e .` 后执行 `sr_paperize --help` 与 T021 同等 smoke；验收：`sr_paperize --help` 退出码 0（验证 P2 工具安装路径）

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ── BLOCKS ──→ Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3)
                                              ↘           ↓              ↓
                                               Final Phase (T018–T022) ←┘
```

- **Phase 2** 必须在 **Phase 3–5** 之前完成（无 `src/simpread_paperize` 则 CLI/测试无法验收）。
- **Phase 4** 的 `pytest`（T014）依赖 **Phase 2** import 与 **Phase 3** CLI 可运行（若测试 subprocess 调用 CLI）。
- **Phase 5** 可与 Phase 4 末尾并行（不同文件：README vs 测试），但 **Final grep（T018）** 应在所有代码与测试改动之后。
- **T013（tests）** 必须在 **T014（pytest）** 之前。

### User Story Dependencies

| 故事 | 依赖 | 独立测试 |
|------|------|----------|
| US1 (P1) | Phase 2 完成 | `uv run sr_paperize --help` |
| US2 (P2) | Phase 2 + US1 建议完成 | `uv run pytest` |
| US3 (P3) | Phase 2 完成；与 US2 文档可并行 | README/契约审阅 |

### Parallel Opportunities

| 可并行任务 | 条件 |
|------------|------|
| T001 ∥ T002 | Setup：`pyproject.toml` 与 `LICENSE` 不同文件 |
| T011 ∥ T012 | US2：确认 `renderer.py` 与 `cleaner/` 无文件间依赖 |
| T016 ∥ T017 | US3：`contracts/cli.md` 与 `quickstart.md` |
| T020 ∥ T021 | Final：spot-check 与 smoke 不同关注点（可同人顺序执行） |

### Parallel Example: Phase 4

```bash
# 确认 renderer 与 cleaner 模块（不同文件树）：
# T011: src/simpread_paperize/renderer.py
# T012: src/simpread_paperize/cleaner/*.py

# 测试文件 import 可并行编辑后一次 pytest：
# T013: tests/test_*.py → T014: uv run pytest
```

---

## Implementation Strategy

### MVP First（仅 US1）

1. Phase 1 → Phase 2（**必须**）
2. Phase 3（US1）：`uv run sr_paperize --help`
3. **停止并验证** — 开发机最小可用

### 完整交付

1. Phase 1–2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Final Phase
2. 每阶段结束执行对应「独立验收」命令
3. 禁止在半迁移状态提交（`src/paperize` 与 `simpread_paperize` 并存且 import 混用）

---

## Task Summary

| 阶段 | 任务 ID | 数量 |
|------|---------|------|
| Phase 1 Setup | T001–T002 | 2 |
| Phase 2 Foundational | T003–T007 | 5 |
| Phase 3 US1 | T008–T009 | 2 |
| Phase 4 US2 | T010–T014 | 5 |
| Phase 5 US3 | T015–T017 | 3 |
| Final Polish | T018–T022 | 5（T022 可选） |
| **合计** | **T001–T022** | **22**（21 必做 + 1 可选） |

**按用户故事**：US1 → 2 项；US2 → 5 项；US3 → 3 项。

**建议 MVP 范围**：Phase 1 + Phase 2 + Phase 3（T001–T009）。

---

## Notes

- 不在此特性中修改 `specs/001-paperize-mvp/**`（可选 follow-up：加废弃注记）。
- `runtime_patch.js` 内 `paperize-table-wide` **不要**改名。
- 若 `uv sync` 失败，先完成 T003–T005 再重试，勿跳过目录迁移直接改 `pyproject`。
