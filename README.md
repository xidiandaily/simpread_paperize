# Paperize

Paperize 是一个**本地离线**工具：把 **简悦（Simpread）** 等工具导出的 **HTML 文章** 清洗并渲染为 **A4 打印友好 PDF**，不依赖系统 Chrome，不上传文件。

## 解决的问题

浏览器里阅读体验好的离线 HTML，用 Chrome 直接打印常出现：版心不适配 A4、阅读器 UI 进 PDF、分页与字体不理想等。Paperize 用 **Python 清洗 DOM + 打印 CSS + Playwright Chromium** 导出 PDF。

## 环境要求

- Python **>= 3.11**
- [uv](https://github.com/astral-sh/uv)

## 安装

```bash
git clone <仓库地址> && cd Paperize
uv sync
uv run playwright install chromium
```

## 使用示例

**单文件**（省略 `-o` 时在同目录生成同名 `.pdf`）：

```bash
uv run paperize example_html/某文章.html -o /tmp/out.pdf
```

**批量**（目录输入必须带 `--out`）：

```bash
uv run paperize ./example_html --out ./pdf --recursive
```

**调试**（生成 `.paperize-debug/<标题>/` 下的 `original.html`、`cleaned.html`、CSS 副本与 `render.log`）：

```bash
uv run paperize article.html -o article.pdf --debug
```

## 开发常用命令

```bash
uv sync
uv run playwright install chromium
uv run paperize --help
uv run pytest
```

## 当前限制（MVP）

- 无 Web UI；无 Docker 镜像（后续可容器化）。
- 纸张首版以 **A4** 为主；极端复杂网页可能转换失败，请用 `--debug` 排查。

## 许可证

（待补充）
