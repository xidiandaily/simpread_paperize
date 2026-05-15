# SR Book 离线 PDF fixtures

测试在本地生成**极简单页 PDF**（不依赖网络），勿提交体积过大的二进制；可在用例内用 `pypdf` 临时写 `tmp_path`。

- 推荐：在 `tests/book/conftest.py` 或各测试内用 `pypdf.PdfWriter` + 空白页写入 `tmp_path / "a.pdf"`。
- 封面 fixture：同样为单页 PDF 即可满足 `plan`/`build` 烟测。
- 路径约定：manifest 内使用相对路径（如 `articles/a.pdf`），相对 `manifest.yaml` 所在目录解析。
