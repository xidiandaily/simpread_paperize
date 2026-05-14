<!--
Sync Impact Report
- Version change: (template placeholders) → 1.0.0
- Modified principles: N/A（首次从模板落地为 Paperize 专用条文）
- Added sections: 技术栈与工程约束；禁止事项、隐私与调试；成功标准（MVP）
- Removed sections: 无
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ Constitution Check 已对齐 Paperize
  - .specify/templates/spec-template.md ✅ 增加 Paperize 语境下的离线/隐私提示
  - .specify/templates/tasks-template.md ✅ Path Conventions 增加 Paperize 包结构提示
  - .specify/templates/commands/*.md ⚠ 目录不存在或无可更新文件，跳过
- Follow-up TODOs: 无
-->

# Paperize Constitution

## Core Principles

### I. 中文优先的用户界面

所有面向用户的说明 MUST 以简体中文为主：CLI 帮助、进度提示、错误信息、日志摘要，以及 README 与快速开始文档。命令与选项名称 MAY 保留英文以保持与生态一致，但其说明文字 MUST 使用中文。日志与终端输出 MUST 避免大段粘贴用户 HTML 正文，以降低隐私泄露风险。

**定位语境**：Paperize 是「离线阅读 HTML 的打印清洗器 + A4 PDF 渲染器」，优先服务简悦（Simpread）等工具导出的离线文章，而非通用网页爬虫或在线 html2pdf 服务。

### II. 可复现的离线转换

项目 MUST 使用 `uv` 管理依赖，并将 `pyproject.toml` 与 `uv.lock` 纳入版本控制。转换管线 MUST 在合理范围内保持确定性：不依赖用户本机已安装的 Chrome/Chromium；Playwright MUST 使用项目安装与锁定的 Chromium 完成渲染与 PDF 导出。默认行为 MUST 不主动联网拉取文章资源；若未来存在可选在线能力，MUST 显式开关且默认关闭。

### III. 只读源文件与安全的输出

用户提供的原始 HTML（含简悦备份）MUST 视为只读输入。清洗后的 HTML、注入样式、调试产物与 PDF MUST 写入用户指定的输出目录或受控的临时目录。覆盖已存在的 PDF 文件 MUST 仅在用户传入 `--overwrite`（或等效显式标志）时发生；默认 MUST 拒绝静默覆盖。输出 PDF 文件名 MUST 经过安全化处理，并正确处理中文、空格与跨平台非法字符。

### IV. 结构清洗优先与分层架构

对简悦等阅读模式 HTML，团队 MUST 优先通过 Python 进行结构级 DOM 清理（BeautifulSoup4 + lxml），再注入 Paperize 打印 CSS；不得仅靠 CSS「硬压」修复结构性问题。打印样式 MUST 主要存放在 `assets/styles/`（或计划中等效目录），禁止将大段 CSS 长期堆在 Python 字符串中。代码 MUST 分层：`cleaner`（识别与清洗）、`renderer`（Playwright 渲染）、`styles`（打印 CSS）、`cli`（命令行）、`config`（参数与默认配置）等职责清晰，禁止将所有逻辑塞进单一 `main.py`。

### V. 可扩展 Cleaner、跨平台与 A4 打印目标

Cleaner 架构 MUST 支持通过 `match()` 判断是否适用、`clean()` 返回标准化 HTML，以便未来扩展 generic HTML、Markdown、Readwise 快照等来源；第一版 MAY 聚焦简悦 HTML，但不得把简悦假设写死到无法插拔其他 Cleaner。路径处理 MUST 使用 `pathlib`；MUST 兼容 macOS 与 Windows，并规划 Docker 运行；禁止硬编码 `/tmp`、Linux 专属路径或依赖 shell 命令拼接路径。默认纸张 MUST 为 A4；默认版式 MUST 适合常见惠普家用/办公打印机，在黑白或彩色打印下正文清晰；背景 MUST 简洁，避免不必要灰底与阴影；正文可读性优先于像素级还原网页视觉效果。MVP 阶段 MAY 对极端复杂页面转换失败，但 MUST 提供清晰的中文错误说明与可选 `--debug` 诊断产物（例如 `original.html`、`cleaned.html`、注入 CSS、渲染相关日志）。

## 技术栈与工程约束

- **语言**：Python >= 3.11。
- **包管理**：`uv`；锁文件与元数据 MUST 可复现安装。
- **CLI**：优先 Typer。
- **HTML**：BeautifulSoup4 + lxml 解析与清洗。
- **渲染**：Playwright + 项目管理的 Chromium 导出 PDF。
- **日志**：`rich` 或标准库 `logging`，以用户可读为先。
- **测试**：pytest；对清洗规则、路径与 CLI 关键路径 SHOULD 有自动化测试。
- **配置**：第一阶段以 CLI 参数为主；后续 MAY 引入 `pyproject` 片段或 `paperize.toml`，变更 MUST 在计划中说明迁移策略。

## 禁止事项、隐私与调试

- 第一版 MUST NOT 引入复杂 Web 服务或默认远程上传用户 HTML/PDF。
- MUST NOT 默认依赖用户已安装的系统浏览器进行渲染。
- MUST NOT 默认联网下载整篇文章资源。
- MUST NOT 在日志中输出大段用户文档原文。
- 提供 `--debug`（或等效）时，MUST 将诊断文件写入明确目录，便于排查版式问题，同时仍遵守「不在普通日志中泄露原文」的约束。

## 成功标准（MVP 对齐）

以下能力构成当前阶段的核心成功标准，规划与任务分解 SHOULD 与之对齐：

1. 单文件：`paperize input.html -o output.pdf`（或等效命令）可完成转换。
2. 目录批处理：`paperize ./simpread-backup --out ./pdf --recursive`（或等效）可批量处理。
3. 在 macOS 上可运行；设计决策 MUST 为后续 Windows 与 Docker 留出空间。
4. 对典型简悦离线 HTML，生成 A4 友好、版式稳定的 PDF。
5. 失败时具备中文错误提示，并在启用调试模式时提供足够材料定位问题。

## Governance

本宪法优先于与之冲突的临时约定或口头习惯。任何修订 MUST：更新本文件正文、按语义化版本规则递增文末版本号、将 `Last Amended` 更新为修订当日（ISO `YYYY-MM-DD`），并在文件顶部 Sync Impact Report 中记录原则与模板联动情况。MAJOR 表示治理原则删除或向后不兼容重定义；MINOR 表示新增原则或实质性扩展指导；PATCH 表示措辞澄清与非语义修订。

合并请求与实现审查 SHOULD 核对：中文用户文案、只读源与输出策略、分层与资源目录约定、离线/隐私边界、以及 Constitution Check（见 `.specify/templates/plan-template.md`）所列门禁。

**Version**: 1.0.0 | **Ratified**: 2026-05-14 | **Last Amended**: 2026-05-14
