# CLI Contract: `sr_book`

与 [data-model.md](../data-model.md) 中的 manifest / `plan.json` schema 一致；Typer 实现细节可调整，**用户可见行为**须一致。

## 命令形态

```text
sr_book init ...
sr_book index ...
sr_book plan ...
sr_book build ...
```

- 一级子命令 **必须且仅能** 为：`init`、`index`、`plan`、`build`。
- 与 `sr_paperize`（`simpread_paperize.cli:app`）并列；入口：`sr_book` → `simpread_paperize.book_cli:app`（`pyproject.toml` `[project.scripts]`）。

## 全局选项（建议）

| 选项 | 类型 | 默认 | 行为 |
|------|------|------|------|
| `--traceback` | flag | off | 失败时打印 Python 堆栈（调试） |

## `sr_book init`

| 参数 / 选项 | 必填 | 说明 |
|-------------|------|------|
| `TARGET_DIR` | 是 | 生成模板的目标目录（不存在则创建） |
| `--force` | 否 | 若 `manifest.yaml` 已存在，允许覆盖（默认 MUST 拒绝覆盖并退出码 1） |
| `--no-scan` | 否 | 不扫描 PDF：始终写入固定教学模板（与早期仅模板行为一致） |
| `--shallow` | 否 | 仅扫描目标目录**根下**的 `*.pdf`；默认会**递归**子目录 |

**行为**：

- **默认（扫描）**：在 `TARGET_DIR` 下递归查找 `*.pdf`（排除占位封面文件 `covers/_sr_book_placeholder_cover.pdf` 自身）。若找到至少一个：写入 **初版** `manifest.yaml`（书名默认取目录名；`trace_header` 为占位中文提示；单卷、`articles` 为排序后的相对路径与篇名=文件名去扩展名），并生成一页空白 **占位封面** PDF（路径见上；已存在则不覆盖）。若目录内**没有任何** PDF：写入静态教学模板（与 `--no-scan` 类似）。
- **`--no-scan`**：不遍历文件，始终写入固定教学模板。

## `sr_book index`

| 参数 / 选项 | 必填 | 说明 |
|-------------|------|------|
| `--manifest`, `-m` | 是 | `manifest.yaml` 路径 |
| `--dry-run` | 否 | 仅打印将执行的重命名映射；**不得**写磁盘、**不得**改 manifest |

**行为**：

- 按 [data-model.md](../data-model.md) 得到全局篇序；仅处理 `.pdf`（扩展名大小写实现可约定为小写校验）。
- 为每篇在磁盘上的文件添加数字前缀（`1_`、`2_`… 与全局序一致）；重命名成功后 **回写** manifest 内对应 `path`。
- **不得**重命名、删除或覆盖 manifest **未列出**的路径；**不得**处理非 PDF。

## `sr_book plan`

| 参数 / 选项 | 必填 | 说明 |
|-------------|------|------|
| `--manifest`, `-m` | 是 | `manifest.yaml` 路径 |
| `--plan-out` | 否 | `plan.json` 输出路径；**默认** `{manifest_dir}/plan.json` |
| `--quiet` | 否 | 若设置：不打印人类表格，仅写 `plan.json`（实现可选） |

**行为**：

- 读取 manifest；解析相对路径；统计各封面、各篇、目录页占位页数；执行分卷与起始页计算。
- stdout：人类可读表格（列含卷号、篇名、篇页数、篇起始物理页、卷总页等，中文列头）。
- 写出 `plan.json`（成功时 `success: true`）；**不得**创建最终合集 PDF。
- 校验失败：stderr 中文可行动文案 + **非零退出**；`plan.json` 可写 `success: false` + `errors[]`（实现须二选一文档化，推荐失败时仍写诊断 JSON 便于 CI）。

## `sr_book build`

| 参数 / 选项 | 必填 | 说明 |
|-------------|------|------|
| `--manifest`, `-m` | 是 | `manifest.yaml` 路径 |
| `--plan` | 否 | `plan.json`；默认 `{manifest_dir}/plan.json` |
| `--output-dir`, `-o` | 是 | 各卷合集 PDF 输出目录 |
| `--overwrite` | 否 | 允许覆盖已存在的目标合集 PDF（默认拒绝，与宪法「静默覆盖」一致） |
| `--temp-dir` | 否 | 中间 PDF 临时目录；**当前实现**主要在内存合并，本参数为预留（与 quickstart 说明一致）；若将来写入中间文件将优先使用该目录 |

**行为**：

- 分卷与起始页 **必须与** `plan` 使用同一实现（共享库函数）；若 `plan.json` 与 manifest 不一致（时间戳/哈希可选），实现 MAY 警告或报错（择一写入 plan 契约）。
- 生成每卷：封面 PDF → 目录页 PDF → 各篇合并；叠加页眉（`book.trace_header`）与左下角「当前页/该卷总页数」；篇级书签；丢弃子 PDF 原书签。
- **不得**修改源单篇 PDF 字节；仅写入新合集文件。

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 1 | 用户输入 / manifest 校验 / 参数错误（路径非法、`..` 越界、缺必填项等） |
| 2 | 运行时错误（IO、PDF 解析、分卷不可行、封面缺失、磁盘满等） |

**预留**：`3` 可预留给「plan 与 manifest 冲突」；若未使用须在实现与本文档保持一致。

## 标准输出 / 标准错误

- 正常进度、表格：**stdout**（中文为主）。
- 错误、警告：**stderr**。
- **禁止**在日志中打印 PDF 提取的正文大块或 base64（宪法 / spec 隐私）。

## 路径与安全

- manifest 内文件路径为相对路径，相对 `manifest_dir`。
- 包含 `..` 或解析后逃出 `manifest_dir` 的路径：**拒绝**（退出码 1）。

## 机器可读错误码（`plan.json` / `errors[].code`）

实现 MUST 稳定使用下列 `code` 字符串（`message` 可中文细化）：

| `code` | 典型场景 | 建议退出码 |
|--------|----------|------------|
| `MANIFEST_PARSE` | YAML 语法错误或缺必填键 | 1 |
| `MANIFEST_SCHEMA` | 字段类型/取值非法 | 1 |
| `PATH_ESCAPE` | 相对路径越出 manifest 目录 | 1 |
| `FILE_NOT_FOUND` | 封面或篇 PDF 不存在 | 2 |
| `NOT_PDF` | 扩展名或内容非 PDF | 2 |
| `ARTICLE_EXCEEDS_VOLUME_CAP` | 单篇页数 > `max_pages_per_volume` | 2 |
| `INSUFFICIENT_VOLUME_SLOTS` | 装箱需卷数 > `len(volumes)` | 2 |
| `INDEX_COLLISION` | 重命名目标已存在或冲突 | 2 |
| `PLAN_IO` | 无法写入 `plan.json` | 2 |
| `BUILD_IO` | 无法写合集或临时文件 | 2 |
| `BUILD_MERGE` | 合并/叠字/书签写入失败 | 2 |
| `PLAN_STALE` | （可选）`plan.json` 与 manifest 不一致 | 1 或 2（实现固定） |
