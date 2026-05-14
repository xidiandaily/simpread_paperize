# Data Model: Paperize MVP

本文描述运行时核心数据结构（Python），与 [spec.md](./spec.md) 实体章节对齐。

## ConvertOptions

用户 CLI / 默认配置解析结果，贯穿单次转换。

| 字段 | 类型 | 说明 |
|------|------|------|
| `input_path` | `Path` | 输入文件或目录 |
| `output_pdf` | `Path \| None` | 单文件模式 `-o`/`--output` |
| `output_dir` | `Path \| None` | 批量模式 `--out` |
| `recursive` | `bool` | `--recursive` |
| `paper` | `str` | 默认 `"A4"` |
| `margin` | `str` | 默认 `"14mm"`，四边可简化为统一值 MVP |
| `debug` | `bool` | `--debug` |
| `overwrite` | `bool` | `--overwrite` |
| `print_background` | `bool` | 默认 `True`，见 research.md |
| `prefer_css_page_size` | `bool` | 默认 `True`，映射 Playwright PDF 选项 |

校验规则（概念）：

- 单文件输入时：允许仅 `-o` 缺省（走默认输出路径）；禁止 `--out` 与 `-o` 同时语义冲突（Typer 层互斥）。
- 目录输入时：必须 `--out`；`--recursive` 影响扫描。

## CleanResult

`BaseCleaner.clean()` 的返回值。

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | `str` | 展示/命名用；简悦来自 `sr-rd-title` |
| `html` | `str` | 标准化后完整 HTML 文档字符串 |
| `source_type` | `str` | 如 `"simpread"` / `"generic"` |
| `warnings` | `list[str]` | 非致命问题中文描述，写入日志或 `render.log` |

不变量：

- `html` MUST 为自包含可加载文档（含 `charset`）；不含原始简悦大段 CSS（见 plan/research）。

## ConvertResult

单次输入文件转换的对外结果（CLI 汇总、批量统计）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `input_path` | `Path` | 源 HTML |
| `output_path` | `Path \| None` | 成功时的 PDF 路径 |
| `success` | `bool` | 是否成功 |
| `message` | `str` | 中文摘要或错误原因（不含大段原文） |
| `debug_dir` | `Path \| None` | `--debug` 时中间产物目录 |

## CleanerRegistry（运行时组件）

| 概念 | 说明 |
|------|------|
| `cleaners` | 有序 `list[BaseCleaner]` |
| `select(html, source_path)` | 返回用于本次的 `BaseCleaner` 实例 |

## 与文件系统的关系

- **Entity「SourceHtml」**：路径 + 可选编码读取结果；不持久化 ORM。
- **DebugBundle**：见 spec；物理目录 `.paperize-debug/<slug>/` 下多文件。

## 状态转换（单次转换）

```text
[CLI 解析] → ConvertOptions
  → 读源 HTML 字符串
  → CleanerRegistry.select → clean → CleanResult
  → 写临时 cleaned.html（可选复制 debug）
  → Renderer.render → PDF
  → ConvertResult
```

批量：对多个 `input_path` 重复上述流水线，聚合 `list[ConvertResult]`。
