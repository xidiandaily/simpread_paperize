# CLI Contract: `paperize`

面向实现与测试的接口约定（Typer 实现细节可调整，**用户可见行为**须一致）。

## 命令形态

```text
paperize [OPTIONS] INPUT_PATH
```

- `INPUT_POSITIONAL`：必填，单个 `.html` / `.htm` 文件路径，或目录路径。

## 选项

| 选项 | 类型 | 默认 | 行为 |
|------|------|------|------|
| `-o`, `--output` | path | 见 research §6 | 单文件输出 PDF 绝对或相对路径 |
| `--out` | path | 无 | 批量输出目录；目录输入时必填 |
| `--recursive` | flag | off | 目录模式下递归收集 `.html`/`.htm` |
| `--paper` | str | `A4` | MVP 仅要求 A4；其他值可报错中文提示「暂不支持」 |
| `--margin` | str | `14mm` | 传入 renderer / PDF；格式错误时中文报错 |
| `--debug` | flag | off | 写入 `.paperize-debug/<slug>/` 约定文件 |
| `--overwrite` | flag | off | 允许覆盖已存在目标 PDF |

## 退出码（建议）

| 码 | 含义 |
|----|------|
| 0 | 全部成功（批量）或单文件成功 |
| 1 | 用户输入/参数错误 |
| 2 | 运行时错误（清洗/渲染/IO），含部分失败时由实现定义：建议「任一失败则非 0」并在 stderr 汇总 |

## 标准输出 / 标准错误

- 进度与结果：**stdout**（中文，人类可读）。
- 错误与警告：**stderr**。
- **禁止**在默认日志中打印整页 HTML 正文（宪法）。

## 批量汇总（stdout 示例结构）

实现可调整措辞，须包含：

- 成功件数、失败件数。
- 每个失败项一行：`路径 — 原因摘要`。

## 与 `ConvertOptions` 映射

见 [data-model.md](../data-model.md)；CLI 层负责解析 Path、布尔与字符串，构造 `ConvertOptions` 调用服务层函数（如 `run_convert(options)`，名称以实现为准）。
