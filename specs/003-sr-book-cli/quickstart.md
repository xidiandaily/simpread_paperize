# SR Book 快速开始

**前提**：已用 `uv` 安装本仓库包；与 `sr_paperize` 独立——`sr_book` 只消费**已有** PDF。

## 1. 安装与入口

```bash
uv sync
# 安装后应存在：
#   sr_paperize  — HTML → 单篇 PDF
#   sr_book      — 多篇 PDF → 多卷合集
```

入口在 `pyproject.toml` 中注册为 `sr_book = "simpread_paperize.book_cli:app"`。

## 2. 典型闭环（编号 → 校验 → 成书）

在**空目录或已有 PDF 的目录**下（示例用 `uv run`，与 `sr_paperize` 一致）：

```bash
# 1) 生成 manifest 模板
uv run sr_book init ./my-book

# 2) 编辑 ./my-book/manifest.yaml：补全书名、trace_header、各卷 cover_pdf、篇 path/title

# 3) 按 manifest 顺序为篇目 PDF 加数字前缀，并回写 manifest
uv run sr_book index -m ./my-book/manifest.yaml
# 仅查看：uv run sr_book index -m ./my-book/manifest.yaml --dry-run

# 4) 分页规划 + 写出 plan.json（默认与 manifest 同目录）
uv run sr_book plan -m ./my-book/manifest.yaml

# 5) 生成各卷合集 PDF（默认不覆盖已存在输出）
uv run sr_book build -m ./my-book/manifest.yaml -o ./my-book/out
# 需要覆盖时：加上 --overwrite
```

## 2.1 最小端到端（本地生成空白 PDF）

以下用 `pypdf` 在 `demo/` 下生成单页占位 PDF（**不联网**），再跑四子命令；思路与 `tests/book/test_build_merge.py` 相同。

```bash
mkdir -p demo/covers demo/articles
uv run python -c "
from pathlib import Path
from pypdf import PdfWriter
for p in [Path('demo/covers/c1.pdf'), Path('demo/articles/a.pdf')]:
    p.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    w.write(p.open('wb'))
"
uv run sr_book init demo
# 将 demo/manifest.yaml 中 cover 改为 covers/c1.pdf、篇目改为 articles/a.pdf 后：
uv run sr_book index -m demo/manifest.yaml
uv run sr_book plan -m demo/manifest.yaml
uv run sr_book build -m demo/manifest.yaml -o demo/out
```

## 3. 离线、隐私与临时文件

- 全流程**不联网**；不读取 URL 资源。
- 日志与错误信息**勿**粘贴 PDF 正文。
- `build` 的 `--temp-dir` 为**预留开关**（当前合并主要在内存完成；与 `contracts/cli.md` 一致）；若后续版本写入中间文件，将优先使用该目录。

## 4. 常见失败与处理

| 现象 | 处理 |
|------|------|
| plan 报单篇页数大于 `max_pages_per_volume` | 拆篇或调高 manifest 中的上限 |
| plan/build 报封面缺失 | 补全 `volumes[].cover_pdf` 指向的文件 |
| plan 报卷数不足（封面槽位不够） | 在 `volumes` 中追加带 `cover_pdf` 的条目 |
| build 报目标已存在 | 删除旧文件或加 `--overwrite` |

## 5. 进一步阅读

- 需求与验收：[spec.md](./spec.md)
- manifest / plan schema：[data-model.md](./data-model.md)
- CLI 与退出码：[contracts/cli.md](./contracts/cli.md)
- PDF 依赖与许可证：[research.md](./research.md)
