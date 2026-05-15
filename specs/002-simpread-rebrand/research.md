# Research: Simpread Paperize 品牌与分发重命名

**Feature**: `002-simpread-rebrand` | **Date**: 2026-05-15

## 1. 为何 CLI 使用 `sr_paperize` 而非 `paperize`

**Decision**: 终端命令定为 **`sr_paperize`**；分发包与 import 根为 **`simpread_paperize`**；不保留 `paperize` 作为 `[project.scripts]` 官方别名。

**Rationale**:

- **PyPI / 生态重名**：`paperize` 为通用英文词，在包索引与 GitHub 上易与其它项目混淆，不利于 `uv tool install` 与长期维护。
- **简悦场景定位**：产品服务于 **Simpread（简悦）** 离线 HTML → A4 PDF；`sr_` 前缀与仓库名 `simpread_paperize` 一致，便于用户识别「简悦系工具链」而非泛用 html2pdf。
- **与内部实现分离**：对外命令改名不影响已稳定的 DOM/CSS 类名（仍用 `paperize-*`），避免大规模版式回归。

**Alternatives considered**:

| 方案 | 放弃原因 |
|------|----------|
| 保留 `paperize` 命令 + 新包名 | 用户仍可能装错旧全局包；与 spec FR-001「仅暴露 sr_paperize」冲突 |
| 命令与包同名 `simpread_paperize` | 终端输入过长；`sr_paperize` 更短且与简悦缩写习惯一致 |
| 同时提供 `paperize` 别名 | spec 明确禁止官方脚本别名，减少双入口文档漂移 |

## 2. 为何保留内部 `paperize-*` CSS/HTML 标识

**Decision**: 不修改 `.paperize-debug/`、样式文件名（如 `paperize-base.css`）、HTML class（`paperize-document`、`paperize-title` 等）、`runtime_patch.js` 中的 class 名、`convert.py` 内对 `paperize-base.css` 的路径引用。

**Rationale**:

- **回归风险**：清洗输出与打印 CSS、Playwright 注入链已针对现有 class 调优；改名需同步改 CSS 选择器、测试 fixture 预期与 debug 产物路径，收益仅为命名一致，成本高。
- **用户不可见**：内部标识不出现在 CLI 帮助、README 安装步骤或 PATH 命令中。
- **spec 边界**：FR-009 与 spec「非目标」明确允许保留。

**Alternatives considered**:

| 方案 | 放弃原因 |
|------|----------|
| 全量改为 `sr_paperize-*` / `simpread-*` | 大范围 diff，易引入分页/字体回归；超出分发重命名范围 |
| 仅改 debug 目录为 `.sr-paperize-debug/` | 破坏现有用户排查习惯与文档；无业务价值 |

## 3. `uv tool install` 推荐命令模板（Git 源安装）

**Decision**: README 与 [quickstart.md](./quickstart.md) 采用下列模板（`<owner>` 为占位符）：

```bash
# 从 Git 安装到用户工具目录（PATH 可用）
uv tool install "simpread_paperize @ git+https://github.com/<owner>/simpread_paperize.git"

# 一次性安装 Playwright Chromium（若尚未安装）
playwright install chromium
# 或：uv tool run --from simpread_paperize playwright install chromium
```

**开发 editable 安装（维护者 smoke）**:

```bash
cd simpread_paperize
uv sync
uv run playwright install chromium
uv tool install -e .
sr_paperize --help
```

**Rationale**:

- `uv tool install` 将控制台脚本安装到隔离工具环境，符合 P2「PATH 中直接运行」。
- 包名与 `pyproject.toml` 的 `project.name` 一致，避免与旧 `paperize` 包冲突。
- Git URL 使用未来仓库名 `simpread_paperize`，与 spec 命名表一致。

**Alternatives considered**:

| 方案 | 放弃原因 |
|------|----------|
| 仅文档 `pip install git+...` | 项目宪法与 MVP 已选定 `uv` 为包管理标准 |
| 本特性上 PyPI | spec 明确推迟；不在本 research 范围 |
| `uv pip install -e .` 作为唯一路径 | 不满足「终端全局 `sr_paperize`」用户故事；可作为开发补充 |

## 4. setuptools 包数据键迁移

**Decision**: `[tool.setuptools.package-data]` 键由 `paperize` 改为 `simpread_paperize`，文件 glob 不变：`assets/styles/*.css`、`runtime_patch.js`。

**Rationale**: 包目录重命名后，资源必须挂到新 distribution 名称下，否则 editable/wheel 安装后找不到 CSS/JS。

## 5. 技术上下文澄清项

本特性技术栈与约束已在 spec 与用户输入中确定：**无 NEEDS CLARIFICATION** 项；上述决策覆盖计划阶段全部未知点。
