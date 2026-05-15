# Simpread Paperize Quickstart（002 重命名后）

**产品**：简悦等离线 HTML → A4 打印友好 PDF 的本地 CLI  
**命令**：`sr_paperize`  
**包名**：`simpread_paperize`

## 环境要求

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv)

---

## 路径 A：开发机（克隆仓库）

```bash
git clone https://github.com/xidiandaily/simpread_paperize.git
cd simpread_paperize
uv sync
uv run playwright install chromium
```

### 运行 CLI

```bash
uv run sr_paperize --help
```

### 单文件转换

```bash
uv run sr_paperize path/to/article.html -o path/to/article.pdf
```

省略 `-o` 时：与源文件同目录生成同名 `.pdf`（已存在且未 `--overwrite` 则报错）。

### 批量转换

```bash
uv run sr_paperize ./html-backup --out ./pdf --recursive
```

### Debug

```bash
uv run sr_paperize article.html -o article.pdf --debug
```

诊断文件位于 `./.paperize-debug/<slug>/`（目录名未因重命名而改变）。

### 测试

```bash
uv run pytest
```

### 可选：editable 全局命令（维护者 smoke）

```bash
uv tool install -e .
sr_paperize --help
sr_paperize tests/fixtures/simpread_min.html -o /tmp/out.pdf
```

---

## 路径 B：用户安装（`uv tool install` + Git）

无需克隆完整开发树，安装发布型工具入口：

```bash
uv tool install "simpread_paperize @ git+https://github.com/xidiandaily/simpread_paperize.git"
playwright install chromium
sr_paperize --help
```

单文件示例：

```bash
sr_paperize ~/articles/note.html -o ~/articles/note.pdf
```

> 若渲染报浏览器缺失，按终端中文提示执行 `playwright install chromium`。

---

## 许可证

仓库根目录 `LICENSE`（MIT）。详见 README「许可证」小节。

---

## 与 MVP 文档的关系

- 功能行为基线：[001-paperize-mvp/spec.md](../001-paperize-mvp/spec.md)
- 历史 CLI 契约（`paperize`）：[001-paperize-mvp/contracts/cli.md](../001-paperize-mvp/contracts/cli.md) — 仅作档案参考
- 当前官方契约：[contracts/cli.md](./contracts/cli.md)

---

## 明确不在本 quickstart

- Docker 运行
- PyPI `pip install simpread_paperize`（后续特性）
