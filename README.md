# Simpread Paperize

仓库：<https://github.com/xidiandaily/simpread_paperize>

本仓库提供两个并列的**本地离线** CLI，不上传文件：

| 命令 | 作用 |
|------|------|
| `sr_paperize` | 把 **简悦（Simpread）** 等导出的 **HTML** 清洗并渲染为 **A4 打印友好单篇 PDF**（不依赖系统 Chrome） |
| `sr_book` | 在**不修改已有单篇 PDF** 的前提下，按 `manifest.yaml` 将多篇 PDF 编排为多卷「合集 PDF」 |

## 解决的问题

**单篇 HTML → PDF**：浏览器里阅读体验好的离线 HTML，用 Chrome 直接打印常出现版心不适配 A4、阅读器 UI 进 PDF、分页与字体不理想等。`sr_paperize` 用 **Python 清洗 DOM + 打印 CSS + Playwright Chromium** 导出 PDF。

**多篇 PDF → 合集**：已有若干单篇 PDF 后，需要按卷分页、统一页眉与可打印目录、合并为多卷文件供打印或电子阅读。`sr_book` 以 `manifest.yaml` 为唯一编排来源，通过 `init` → `index` → `plan` → `build` 完成「编号 → 校验 → 成书」闭环。

## 环境要求

- Python **>= 3.11**
- [uv](https://github.com/astral-sh/uv)

## 安装

### 从 Git 克隆（开发）

```bash
git clone https://github.com/xidiandaily/simpread_paperize.git
cd simpread_paperize
uv sync
uv run playwright install chromium
```

### 全局工具安装（推荐个人使用）

```bash
uv tool install "simpread_paperize @ git+https://github.com/xidiandaily/simpread_paperize.git"
playwright install chromium
```

> `playwright install chromium` 仅 **`sr_paperize` 渲染**需要；`sr_book` 只处理已有 PDF，无需浏览器。
>
> 若 `sr_paperize` 报浏览器缺失，按终端中文提示执行 `playwright install chromium`（每个环境通常只需一次）。

## 使用示例：`sr_paperize`

**单文件**（省略 `-o` 时在同目录生成同名 `.pdf`）：

```bash
uv run sr_paperize example_html/某文章.html -o /tmp/out.pdf
# 或已 tool install 后：
sr_paperize example_html/某文章.html -o /tmp/out.pdf
```

**批量**（目录输入必须带 `--out`）：

```bash
uv run sr_paperize ./example_html --out ./pdf --recursive
```

**调试**（生成 `.paperize-debug/<标题>/` 下的 `original.html`、`cleaned.html`、CSS 副本与 `render.log`）：

```bash
uv run sr_paperize article.html -o article.pdf --debug
```

## 使用示例：`sr_book`

**前提**：目录中已有单篇 PDF（通常由 `sr_paperize` 或其它工具生成）。`init` 默认会**递归扫描**目标目录中的 `*.pdf` 写入初版 `manifest.yaml`；无 PDF 时写入静态教学模板。

**典型闭环**（编号 → 校验 → 成书）：

```bash
# 1) 生成 manifest（仅根目录：--shallow；不扫描固定模板：--no-scan）
uv run sr_book init ./my-book

# 2) 编辑 ./my-book/manifest.yaml（书名、封面路径、篇目、分卷上限等）

# 3) 按 manifest 顺序为篇目 PDF 加数字前缀，并回写 manifest
uv run sr_book index -m ./my-book/manifest.yaml
# 仅预览：uv run sr_book index -m ./my-book/manifest.yaml --dry-run

# 4) 分页规划，写出 plan.json（默认与 manifest 同目录）
uv run sr_book plan -m ./my-book/manifest.yaml

# 5) 生成各卷合集 PDF（默认不覆盖已存在输出）
uv run sr_book build -m ./my-book/manifest.yaml -o ./my-book/out
# 需要覆盖：加上 --overwrite
```

已 `uv tool install` 后，将上述 `uv run sr_book` 换成 `sr_book` 即可。

更完整的参数、最小端到端示例与常见错误见 [`specs/003-sr-book-cli/quickstart.md`](specs/003-sr-book-cli/quickstart.md)。

## 开发常用命令

```bash
uv sync
uv run playwright install chromium
uv run sr_paperize --help
uv run sr_book --help
uv run pytest
```

## 当前限制（MVP）

- 无 Web UI；无 Docker 镜像（后续可容器化）。
- `sr_paperize`：纸张首版以 **A4** 为主；极端复杂网页可能转换失败，请用 `--debug` 排查。
- `sr_book`：编排完全依赖手改 `manifest.yaml`；单篇页数超过每卷上限时需拆篇或调高 `max_pages_per_volume`（详见 quickstart 故障表）。

## 许可证

本项目采用 [MIT License](LICENSE) 发布。
