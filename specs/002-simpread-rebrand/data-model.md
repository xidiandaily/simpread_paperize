# Data Model: Simpread Paperize 重命名（002）

**Feature**: `002-simpread-rebrand` | **Date**: 2026-05-15

## 结论

**本特性无数据模型变更。**

运行时结构（`ConvertOptions`、`CleanResult`、`ConvertResult`、`BaseCleaner` 契约）与字段语义与 [001-paperize-mvp/data-model.md](../001-paperize-mvp/data-model.md) 完全一致。重命名仅影响：

- Python **import 路径**（`paperize.*` → `simpread_paperize.*`）
- CLI **入口名称**（`paperize` → `sr_paperize`）
- 分发 **包名**（`paperize` → `simpread_paperize`）

## 实体引用（不变）

| 实体 | 变更 |
|------|------|
| `ConvertOptions` | 无字段增删 |
| `CleanResult` | 无 |
| `ConvertResult` | 无 |
| Cleaner 注册与 `match()`/`clean()` | 无 |

## 校验规则

仍由 Typer CLI 层与 `convert.py` 执行，规则见 `001` data-model 与 [contracts/cli.md](./contracts/cli.md)。

## 实现注意

测试与文档中若出现 `paperize-title` 等字符串，指 **HTML/CSS 输出 class**，不是 Python 包名；与 FR-009 一致，不属于数据模型变更。
