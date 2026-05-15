# Feature Specification: Simpread Paperize 品牌与分发重命名

**Feature Branch**: `002-simpread-rebrand`

**Created**: 2026-05-15

**Status**: Draft

**Input**: 将现有 Paperize 项目完成品牌与分发层重命名，以便个人部署与同类用户通过 `uv tool install` 使用；功能行为与 `001-paperize-mvp` 一致，不改变清洗/渲染核心逻辑。

> **Paperize 语境**: 本特性为工程与分发变更，不改变宪法中的产品能力边界（离线、只读源文件、中文 CLI、日志不泄露正文）。对外仍定位为简悦等离线 HTML → A4 PDF 的本地 CLI；内部 HTML/CSS 类名、样式文件名与 `.paperize-debug/` 调试目录保持既有命名以稳定实现。

## 概述

**一句话**：将项目从「Paperize / paperize」统一重命名为「Simpread Paperize / simpread_paperize / sr_paperize」，使维护者与用户可通过 Git 克隆与 `uv tool install` 安装，并在 PATH 中使用新命令完成与 MVP 相同的转换。

**用户画像**：项目维护者（本地开发与 CI）、通过 Git 安装工具的个人用户、阅读 README 了解安装步骤的潜在用户。

**产品目标**

1. 对外标识与仓库、包、命令命名一致，避免与泛称「paperize」混淆。
2. 支持 `uv sync` 开发运行与 `uv tool install` 从 Git 安装两种分发路径。
3. README 清晰说明定位、安装、MIT 许可与 Playwright Chromium 一次性安装。
4. 转换能力（单文件、批量、`--debug`、`--overwrite` 等）与 `001-paperize-mvp` 无行为回归。

**非目标（本特性）**

1. 不重写 SimpreadCleaner、renderer 或 Playwright 渲染逻辑。
2. 不将 HTML/CSS 内部类名（如 `paperize-document`、`paperize-title` 等）改为新前缀。
3. 不将调试目录 `.paperize-debug/`、样式资源文件名（如 `paperize-base.css`）改名。
4. 不上传 PyPI（仅保证元数据与 Git 安装路径正确；PyPI 发布可作为后续可选特性）。
5. 不新增 Web 服务、在线能力或产品功能扩展。

**命名对照（必须达成）**

| 维度 | 目标名称 |
|------|----------|
| Git 仓库名 | `simpread_paperize` |
| 分发包名（PyPI / uv） | `simpread_paperize` |
| Python 包 import 根 | `simpread_paperize`（源码目录 `src/simpread_paperize/`） |
| 终端命令 | `sr_paperize`（取代原 `paperize`） |
| 产品对外称呼 | README 使用「Simpread Paperize」或「sr_paperize」 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 维护者本地开发与帮助 (Priority: P1)

作为维护者，我在仓库根目录执行依赖同步后，可通过 `uv run sr_paperize --help` 查看**简体中文**帮助，确认新命令与包名已生效。

**Why this priority**：开发闭环是后续测试、文档与 Git 安装验证的前提；帮助文案是用户首次接触产品的入口。

**Independent Test**：在干净虚拟环境中 `uv sync`，仅执行 `uv run sr_paperize --help`，检查退出码为 0 且输出为中文说明。

**Acceptance Scenarios**:

1. **Given** 已克隆 `simpread_paperize` 仓库且依赖已同步，**When** 维护者执行 `uv run sr_paperize --help`，**Then** 显示中文帮助且列出与 MVP 一致的核心选项（单文件、输出、批量、调试、覆盖等）。
2. **Given** 帮助已更新，**When** 维护者查阅示例命令，**Then** 文档与帮助中用户可见示例均使用 `sr_paperize`，不出现 `paperize` 作为推荐命令。

---

### User Story 2 - 用户通过 Git 安装并使用 (Priority: P2)

作为用户，我通过 `uv tool install` 从 Git 仓库安装 `simpread_paperize` 后，可在任意目录直接运行 `sr_paperize`，完成与 MVP 相同的单文件 HTML → PDF 转换。

**Why this priority**：本特性的核心价值是支持个人部署与同类用户的标准化安装路径。

**Independent Test**：在未加入开发依赖的环境中，仅从 Git URL 安装工具，对既有测试 fixture 执行单文件转换并验证 PDF 生成。

**Acceptance Scenarios**:

1. **Given** 用户已安装 Playwright Chromium（按 README 一次性步骤），**When** 用户执行 `uv tool install "simpread_paperize @ git+https://github.com/xidiandaily/simpread_paperize.git"` 且安装成功，**Then** `sr_paperize` 出现在 PATH 且 `--help` 可用。
2. **Given** 典型简悦离线 HTML fixture，**When** 用户执行 `sr_paperize input.html -o output.pdf`（或等效参数），**Then** 在指定路径生成可打开的 PDF，版式与 MVP 基线一致（smoke 级验证）。
3. **Given** 用户尝试使用旧命令名，**When** 仅安装本特性交付物且未配置别名，**Then** 系统不提供 `paperize` 作为官方入口（无 `project.scripts` 中的 `paperize` 条目）。

---

### User Story 3 - 读者通过 README 完成上手 (Priority: P3)

作为读者，我打开 README 即可了解产品定位、仓库克隆目录名、`uv run` / `uv tool install` 安装方式、MIT 许可证与 Playwright Chromium 安装提醒。

**Why this priority**：降低安装失败与支持成本，与 P2 安装路径形成闭环。

**Independent Test**：人工或检查清单审阅 README 是否包含必需章节且无过时 `paperize` 用户命令示例。

**Acceptance Scenarios**:

1. **Given** 新用户阅读 README，**When** 按「克隆 → uv sync / tool install → playwright install chromium」顺序操作，**Then** 能在无额外口头说明下找到全部步骤。
2. **Given** README 许可证小节，**When** 用户查找许可信息，**Then** 可见 MIT 许可说明且仓库根目录存在 `LICENSE` 文件。
3. **Given** 历史 spec 或开发文档仍提及 `paperize`，**When** 作为用户面向文档呈现，**Then** 须标注旧命令已废弃并指向 `sr_paperize`。

---

### Edge Cases

- 用户已全局安装旧包名 `paperize`：本特性不强制卸载；README 可简短说明新旧包/命令并存时的区别（可选一句，非阻塞）。
- 从旧分支或 fork 合并时残留 `from paperize` import：验收以全仓 grep 与 pytest 为准，须为零残留。
- 远程仓库已确定为 `xidiandaily/simpread_paperize`；README 与 quickstart 使用对应 HTTPS / `git+https` URL。
- Windows / macOS 路径与中文文件名：重命名后行为须与 MVP 一致（继承宪法 III）。
- 无 `LICENSE` 的历史仓库：本特性须新增 MIT `LICENSE` 并在 README 引用。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 项目分发元数据 MUST 将包名设为 `simpread_paperize`，且控制台脚本仅暴露 `sr_paperize` 入口（映射至 CLI 应用），不得保留 `paperize` 官方脚本别名。
- **FR-002**: Python 源码 MUST 自 `src/simpread_paperize/` 布局发布，且全仓（含测试）import 根为 `simpread_paperize`，不得残留 `from paperize` / `import paperize`。
- **FR-003**: 包数据（如打印样式、运行时补丁等资源）MUST 随 `simpread_paperize` 包名正确打包，安装后资源可被运行时加载。
- **FR-004**: CLI 帮助、进度与错误信息 MUST 保持简体中文为主；帮助中的命令示例 MUST 使用 `sr_paperize`。
- **FR-005**: README MUST 说明：产品定位为简悦等离线 HTML → A4 PDF 的本地 CLI；Git 仓库名 `simpread_paperize`；`uv run` 与 `uv tool install git+...` 安装示例；Playwright Chromium 一次性安装步骤。
- **FR-006**: 仓库根目录 MUST 包含 MIT `LICENSE`，README 许可证小节 MUST 引用 MIT。
- **FR-007**: 单文件转换、目录批量（含递归）、`--debug`、`--overwrite` 及失败时中文错误提示 MUST 与 `001-paperize-mvp` 验收行为一致，不得因重命名而回归。
- **FR-008**: 自动化测试套件 MUST 全部通过；测试代码与 fixture 引用 MUST 使用新包名与新命令（如通过 CLI 调用或 import 路径）。
- **FR-009**: 内部实现稳定的标识（HTML/CSS 类名、`paperize-base.css`、`.paperize-debug/` 等）MAY 保持原名，不在本特性范围内强制重命名。

### Key Entities

- **分发包（Distribution Package）**: 用户通过 uv/pip 安装的 `simpread_paperize` 单元，含元数据、入口脚本与捆绑资源。
- **CLI 命令（sr_paperize）**: 用户调用的终端入口，参数语义与 MVP 的 `paperize` 命令一致。
- **文档工件（README / LICENSE）**: 对外安装与合规说明；用户面向命令示例以 `sr_paperize` 为准。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 维护者在依赖同步后，可在 1 分钟内通过 `uv run sr_paperize --help` 获得完整中文帮助（退出码 0）。
- **SC-002**: 从 Git 完成 `uv tool install` 的用户，在不修改 PATH 的前提下可在 5 分钟内完成对既有 fixture 的单文件转换并得到可打开 PDF（smoke）。
- **SC-003**: 全仓源码与测试中，`from paperize` / `import paperize` 的匹配数为 0（自动化 grep 验收）。
- **SC-004**: `uv run pytest` 在重命名后的代码库上 100% 通过（与 MVP 基线测试数量一致或仅因路径/命令字符串更新而调整）。
- **SC-005**: README 审阅清单：克隆目录名、双安装路径、MIT、Chromium 安装四要素齐全；用户面向命令示例中无未标注废弃的 `paperize` 推荐用法。
- **SC-006**: 批量转换与 `--overwrite` / `--debug` 各至少 1 条自动化或文档化验收场景仍可通过（继承 MVP，不因重命名失效）。

## Assumptions

- 目标 Git 远程为 `https://github.com/xidiandaily/simpread_paperize.git`（SSH：`git@github.com:xidiandaily/simpread_paperize.git`）。
- 用户已安装 `uv` 与 Python >= 3.11，与宪法及 MVP 一致。
- Playwright Chromium 仍由用户按 README 执行一次性 `playwright install chromium`（或项目文档约定的等效步骤）。
- 本特性合并后，开发工作主要在 `002-simpread-rebrand` 特性分支进行，与 Speckit 分支约定一致。
- PyPI 公开发布推迟至后续特性；本特性仅保证 `pyproject` 中 `project.name` 与 Git 源安装兼容。
- 宪法原则（中文 CLI、离线、只读源、日志不泄露正文）在重命名过程中保持不变，无需修订宪法版本。

## Dependencies

- **001-paperize-mvp**: 功能行为与验收场景的基线；本特性不得削弱其已交付能力。
- **`.specify/memory/constitution.md`**: 工程治理边界（中文界面、离线、隐私等）继续适用。

## Out of Scope (Explicit)

- SimpreadCleaner / renderer / Playwright 管线逻辑重写。
- 内部 CSS 类名、样式文件名、`.paperize-debug/` 目录名变更。
- PyPI 上传与版本发布流水线（可记录为后续特性）。
- 新命令别名 `paperize` 的保留或兼容层（除非未来单独 spec 批准）。
