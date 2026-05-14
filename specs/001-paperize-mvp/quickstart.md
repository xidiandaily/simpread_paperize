# Paperize MVP Quickstart

## 环境要求

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) 已安装

## 安装

```bash
cd /path/to/paperize
uv sync
uv run playwright install chromium
```

> 若渲染报浏览器缺失，按终端中文提示执行 `playwright install chromium`。

## 单文件转换

```bash
uv run paperize examples/article.html -o out/article.pdf
```

默认输出（省略 `-o` 时）：与源文件同目录、同名 `.pdf`（已存在且未 `--overwrite` 则报错）。

## 批量转换

```bash
uv run paperize ./simpread-backup --out ./pdf --recursive
```

## Debug

```bash
uv run paperize article.html -o article.pdf --debug
```

在 `./.paperize-debug/<slug>/` 查看 `original.html`、`cleaned.html`、CSS 副本与 `render.log`。

## 运行测试

```bash
uv run pytest
```

## 后续：Docker（预留）

方向：基于 `mcr.microsoft.com/playwright/python` 或 `python:3.11-slim`，复制项目后 `uv sync`、`playwright install chromium`，入口仍为 `paperize`。首版不随仓库交付 Dockerfile。
