# Phase 0 Research: Paperize MVP

## 1. Playwright PDF 与本地 `file://` 加载

**Decision**: 使用 `pathlib.Path.as_uri()` 将清洗后的 HTML 绝对路径转为 `file://` URL，调用 `page.goto(uri)`；导出使用 `page.pdf()`，`format="A4"`，`margin` 自 `ConvertOptions` 映射为 Playwright 接受的 dict（`top`/`right`/`bottom`/`left` 字符串如 `14mm`）。

**Rationale**: 官方支持 `file://`；`as_uri()` 在 Windows 上正确处理驱动器与空格。

**Alternatives considered**: `set_content()` 直接塞 HTML——大文件与相对资源路径处理更复杂，首版优先写临时 `cleaned.html` + `file://` 一致于 debug 可打开需求。

## 2. 临时 `cleaned.html` 与 debug 目录

**Decision**:

- 正常运行：将 `cleaned.html` 写入 `tempfile.TemporaryDirectory()` 或系统临时目录下的唯一子目录，转换结束后删除（`debug=True` 时额外复制到 `.paperize-debug/<slug>/`）。
- **slug**：由 `safe_filename(title)` 或源文件 stem 派生，冲突时追加短哈希后缀。
- **debug 目录根**：默认当前工作目录下的 `.paperize-debug/`（与用户需求一致）；在 CLI 中可用 `--debug-dir` 后续扩展，MVP 不强制。

**Rationale**: 满足「不修改源文件」与「debug 可浏览器打开 cleaned」；隐藏目录减少与用户文档混淆。

**Alternatives considered**: 仅内存不落地——与「debug 落盘 cleaned」及排障体验冲突。

## 3. `print_background` 与宪法「背景简洁」

**Decision**: `ConvertOptions.print_background` 默认 **`True`**（与 Playwright 常见代码块/高亮场景一致），通过 **CSS** 抑制大面积灰底（`body`/`main` 背景白、简悦残留容器背景重置）；若个别文章仍发灰，用户可在后续配置中改为 `False`。

**Rationale**: 与用户提供渲染参数一致；版式主导权在 CSS，符合「清洗优先、样式分层」。

**Alternatives considered**: 默认 `False` 更省墨但易丢代码配色——MVP 优先可读，接受 CSS 约束背景。

## 4. Cleaner 选择：`CleanerRegistry`

**Decision**: 注册顺序 `[SimpreadCleaner, GenericCleaner]`；第一个 `match(html)` 为真者胜出；`GenericCleaner.match` 恒真或仅作兜底。

**Rationale**: 可扩展新来源 Cleaner 插入队列前部。

**Alternatives considered**: 单例 if-else——违反可扩展宪法。

## 5. 标准 HTML 骨架与原始 `head` 内简悦 CSS

**Decision**: **不**复用原 `head` 中大段简悦样式；生成最小 `head`：`meta charset="utf-8"`、可选 `<title>`、`<link rel="stylesheet" href="file:///.../paperize-base.css">` 等——实际注入时更稳妥做法为：`page.add_style_tag` / `add_init_script` 读入 CSS 文件内容注入，避免多文件相对路径在 `file://` 下失效。即：**链接式或内联式二选一**；首版推荐 **Python 读 CSS 字符串经 `add_style_tag` 注入**，`cleaned.html` 内仅保留语义结构 + 可选内联 `<style>` 极小片段。若采用外链，`href` 必须为绝对 `file` URI（研究结论：实现任选其一，须在 `renderer` 内统一）。

**Rationale**: 避免简悦 CSS 进入打印流导致错乱（spec/US3）。

**Alternatives considered**: 保留原 head——与清洗目标冲突。

## 6. 单文件未指定 `-o` 时的默认输出路径

**Decision**: 默认输出与源文件同目录，`stem` 相同扩展名 `.pdf`；若已存在且未 `--overwrite`，**失败并中文提示**（与 spec「不静默覆盖」一致）。

**Rationale**: 符合常见 CLI 直觉；与 FR 对齐。

**Alternatives considered**: 输出到 cwd——易与用户预期不符。

## 7. 批量模式输出命名

**Decision**: 优先 `CleanResult.title` 经 `safe_filename`；若空或非法则回退源文件 `stem`；碰撞时追加 `_2`、`_3` 或短哈希。

**Rationale**: 满足 spec US2 与中文文件名安全。

## 8. Playwright 未安装浏览器

**Decision**: 捕获启动/导出异常，中文提示：`请运行：uv run playwright install chromium`（或项目文档中的等价命令）。

**Rationale**: 与风险应对一致。

## 9. Docker（预留）

**Decision**: 首版不交付 Dockerfile；在 `quickstart.md` 保留「后续镜像基于 `mcr.microsoft.com/playwright/python` 或 `python:slim` + `uv sync` + `playwright install chromium`」方向。

**Rationale**: 满足「阶段 8 预留」而不扩大 MVP。
