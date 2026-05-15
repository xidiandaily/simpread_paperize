# Data Model: SR Book（manifest / plan / 运行时对象）

**特性目录**: `specs/003-sr-book-cli/` | **规范**: [spec.md](./spec.md)

## 1. 路径与基准目录

- **`manifest_dir`**：`manifest.yaml` 所在目录（`Path`）。
- **解析规则**：manifest 内所有指向文件的字段 MUST 为 **相对路径**（POSIX 风格字符串推荐），解析为 `manifest_dir / relative`。
- **禁止**：manifest 内使用 `..` 跳出 `manifest_dir` 的路径（实现 MUST 拒绝或规范化后仍须在 manifest 目录树内——与 `contracts/cli.md` 一致）。

## 2. Manifest（YAML）— 权威编排源

顶层键与语义（字段名实现可微调，**语义**须一致；YAML 类型如下）。

| 键 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `schema_version` | int | 是 | 当前文档 schema 版本，v1 建议 `1` |
| `book` | map | 是 | 全书元数据 |
| `book.title` | str | 是 | 书名（用于日志、可选写入元数据） |
| `book.trace_header` | str | 是 | 合集页眉完整字符串（用户配置，如批次/追溯 ID） |
| `max_pages_per_volume` | int | 否 | 每卷最大**物理页数**（含封面 + 目录页 + 正文），默认 `400` |
| `toc_pages_per_volume` | int | 否 | 每卷插入的**可打印目录**页数，默认 `1`（plan/build 须使用同一默认值或显式配置） |
| `volumes` | seq | 是 | 分卷**封面**序列：每一项提供该卷（或潜在卷）的封面；**篇目全局顺序**由下列拼接决定 |
| `volumes[].id` | int \| str | 否 | 卷标识（可选，便于人类阅读） |
| `volumes[].cover_pdf` | str | 是 | 该列表项对应的封面 PDF，相对 `manifest_dir` |
| `volumes[].articles` | seq | 否 | 该项下的篇目列表，允许为空；**全局篇序** = 按 `volumes` 数组顺序，将各 `articles` 依次拼接（用户在多卷下拆分书写时，须理解顺序即 plan/build 消费顺序） |
| `volumes[].articles[].title` | str | 是 | 打印目录与篇级书签显示名 |
| `volumes[].articles[].path` | str | 是 | 单篇 PDF，相对 `manifest_dir` |

**`index` 子命令之后**：所有篇目 `path` MUST 与磁盘上重命名后的文件名一致（工具回写 YAML）。

**分卷与封面条数（与算法一致）**：`plan`/`build` 对「全局篇序」做贪心装箱（整篇入卷、超 `max_pages_per_volume` 则下一卷）。输出第 `k` 卷使用 manifest 中 `volumes[k-1].cover_pdf` 作为封面。若装箱所需卷数 **大于** `len(volumes)`，MUST 报错，提示用户在 `volumes` 中**追加**带 `cover_pdf` 的条目（可暂挂空 `articles`）以提供额外封面槽位。

### 校验规则（plan / build 共用）

- `max_pages_per_volume >= 1`；`toc_pages_per_volume >= 1`。
- 每个 `cover_pdf` 与篇目 `path` 指向的文件必须存在且为可读 PDF。
- 任一篇 `pages > max_pages_per_volume` → **错误**（无法整篇入任一卷）。
- 贪心装箱后所需卷数 **大于** `len(volumes)` → **错误**（封面槽位不足，须扩展 `volumes`）。
- 分卷算法：**不得**拆篇；当前卷已占 + 下一篇整篇若超过 `max_pages_per_volume`，则该篇移至下一卷并使用下一 `volumes[]` 条目的封面。

### 页数模型（规划用）

设 **输出卷** 由贪心装箱得到，第 `v` 卷（1-based）使用 manifest 中 `volumes[v-1].cover_pdf` 作为封面。

对每一**输出**卷 `v`：

- `cover_pages(v)` = 该卷封面 PDF 页数（读取文件）
- `toc_pages(v)` = manifest 的 `toc_pages_per_volume`（须与 `toc_pdf` 生成页数一致）
- 对卷内每篇 `a`：`article_pages(a)` = 该单篇 PDF 页数

**卷内物理页序**：封面（合集第 1 页起）→ 目录页 → 按该卷内篇序拼接各篇。

**起始页**：第一篇在卷内起始页 = `cover_pages + toc_pages + 1`（若封面多页则顺延；默认封面多为 1 页）。

## 3. Plan 输出（JSON，`plan.json`）

与终端表格 **语义一致** 的结构化结果。建议顶层：

| 键 | 类型 | 说明 |
|----|------|------|
| `schema_version` | int | 如 `1` |
| `manifest_path` | str | 解析时使用的 manifest 绝对路径或规范相对路径（实现二选一须在 contracts 固定） |
| `max_pages_per_volume` | int | 复制自 manifest |
| `toc_pages_per_volume` | int | 复制自 manifest |
| `success` | bool | `plan` 成功为 `true`；失败时可选仍写出诊断 JSON 或仅 stderr（contracts 固定一种） |
| `volumes` | seq | 与 manifest 卷顺序一致 |

**`volumes[]` 元素**：

| 键 | 类型 | 说明 |
|----|------|------|
| `volume_index` | int | 1-based |
| `cover_pdf` | str | 相对路径（与 manifest 一致） |
| `cover_pages` | int | |
| `toc_pages` | int | |
| `total_pages` | int | 该卷总物理页数 |
| `articles` | seq | 该卷内篇目（仅含本会纳入的篇） |

**`volumes[].articles[]` 元素**：

| 键 | 类型 | 说明 |
|----|------|------|
| `title` | str | 篇名 |
| `path` | str | 相对 manifest_dir |
| `pages` | int | 该篇 PDF 页数 |
| `start_page` | int | 该篇在**本卷输出合集 PDF** 内的起始物理页码（该文件内封面为第 1 页；与阅读器打开该卷文件时显示的页码一致） |

**错误响应（`success: false` 或进程非零退出）**：包含 `errors[]`：`{ "code": str, "message": str, "path": str | null }`（见 contracts 错误码表）。

## 4. 运行时对象（实现参考，非持久化）

- **`ManifestModel`**：解析 + 校验后的结构体 / dataclass。
- **`VolumePlan`**：一卷内文章列表及预计算 `start_page`、`total_pages`。
- **`BookPlan`**：全部 `VolumePlan` + 全局校验结果。
- **`IndexRenameOp`**：`old_relative`、`new_relative`，用于 dry-run 打印与事务性重命名。

## 5. 与 `sr_paperize` 边界

- **不**导入 Playwright 渲染管线；仅 `Path` 打开已有 PDF。
- 单篇 PDF 来源可为 `sr_paperize` 产出；字段与命名不在本模型强制。
