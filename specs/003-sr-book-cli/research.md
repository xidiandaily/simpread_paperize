# Phase 0 Research: SR Book（多卷合集 PDF）

**特性**: `003-sr-book-cli` | **日期**: 2026-05-16

## 1. PDF 依赖选型（页数、合并、书签、目录页、页眉页脚）

### 候选

| 库 | 许可证（摘要） | 典型 wheel 体积量级 | 能力与本特性匹配度 |
|----|----------------|---------------------|-------------------|
| **pypdf** | BSD-3-Clause（宽松） | 小（纯 Python，依赖面窄） | 读页数、合并、写入 Outline（篇级书签）、在页面上叠加内容可通过 `merge_page`/`Transformation` 等组合实现；生态成熟、无原生二进制 |
| **PyMuPDF (fitz)** | **AGPL-3.0**（开源分发强约束；商业需单独授权） | 大（平台相关二进制 wheel） | 页数/合并/书签/绘图叠字一条链路过关；API 强，但合规与安装体积成本高 |
| **pikepdf** | MPL-2.0（文件级修改友好） | 中（依赖 QPDF 库） | 适合结构修复与部分高级操作；合并+全书版式叠加仍常需与其它生成手段组合 |
| **reportlab** | BSD 风格（以发布 tarball 为准） | 中 | 生成「打印目录页」矢量 PDF 与简单页眉页脚条带非常直接；与 pypdf 组合常见 |

### 决策

- **采用：`pypdf` + `reportlab` 作为 v1 默认组合。**
- **Rationale**
  - **许可证**：`pypdf` 与 `reportlab` 均为宽松许可，便于与现有 `simpread_paperize` 包同仓分发，避免 PyMuPDF 的 **AGPL** 对下游分发/闭源打包的意外约束。
  - **体积**：相较 PyMuPDF 的大体积平台 wheel，**减小安装包与 CI 缓存压力**，符合「体积评估」诉求。
  - **能力拆分**：`pypdf` 负责页数统计、按卷合并、丢弃子书签后写入篇级 Outline；`reportlab` 负责生成可打印目录页 PDF（及可选的简单条带型 overlay 页）；叠加逻辑在实现层以「每页与 A4/源页 MediaBox 对齐」为验收约束（详见 `plan.md` / `data-model.md`）。
- **Alternatives considered**
  - **PyMuPDF**：实现路径最短，但 AGPL + 大体积与宪法「默认可复现、低风险合规」目标冲突风险更高；保留为 **若 pypdf 叠字在极端 PDF 上大面积失败时的备选**，切换前须重新评估许可证与发布形态。
  - **仅 pypdf + 自绘 PDF 字节**：可省 reportlab，但维护成本高；**不推荐**。
  - **pikepdf 为主**：对「生成目录页」仍缺高层绘图 API，最终仍可能引入 reportlab 或类似库；v1 **不引入**，除非 pypdf 在合并/书签上遇到无法接受的 bug。

### 版本与锁

- 在 `pyproject.toml` 中声明下界版本（如 `pypdf>=5` 以获较新 API），由 **`uv lock`** 固定可复现解析。
- **不**在 plan/build 路径引入网络拉取字体或模板；目录页字体使用 reportlab 内置或项目随附字体（若后续增强，须在规格/宪法框架内默认离线）。

## 2. CLI 框架与入口

- **Typer**：与 `sr_paperize`（`simpread_paperize.cli:app`）一致，本特性新增 **`sr_book` → `simpread_paperize.book_cli:app`**（或 `book/cli.py` 再导出 `app`），两入口并列注册于 `[project.scripts]`。
- 子命令固定四个：`init`、`index`、`plan`、`build`；共享 `err_console`/`Console` 模式与现有 CLI 一致，中文帮助与错误（宪法 I）。

## 3. 与宪法条款的逐项关系

| 宪法原则 | 本特性落点 |
|----------|------------|
| 中文优先 | 四子命令 `--help`、校验失败信息、表格列标题中文 |
| 可复现离线 | 不调用网络；依赖仅经 uv 锁定；不读取系统浏览器 |
| 只读源与安全输出 | **不修改**用户单篇 PDF；合集与 `plan.json` 写入显式目录；合集覆盖行为与 `sr_paperize` 对齐：**默认不覆盖**，`--overwrite` 显式允许 |
| 分层 | `book_cli` → `manifest` / `paths` / `volume_plan` / `toc_pdf` / `merge_build` 等模块拆分，禁止单文件堆叠全部逻辑 |
| 日志隐私 | 错误信息引用路径与页数，**禁止**打印 PDF 文本内容或 base64 大块 |

## 4. 测试策略（与用户需求对齐）

- **单元测试优先**：分卷贪心算法（整篇入卷、超限则下一卷）、`plan` 结构化输出与表格字段一致、manifest 相对路径解析、`index` 重命名与 YAML 回写（含 `--dry-run` 无副作用）。
- **契约测试**：`contracts/cli.md` 中退出码与必选/可选选项在测试中抽样覆盖。

## 5. 未决项（v1 不阻塞）

- 极宽/极矮非 A4 单篇与 overlay 对齐的像素级验收：以「阅读器可见页眉左下角、目录页可读」为准，极端样例可后续迭代。
