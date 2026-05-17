请为我生成一套「书籍封面」的单页 HTML + CSS，用于在浏览器中预览，满意后我会用 Chrome「打印 → 另存为 PDF」（A4），再用于个人打印合集。请严格遵守以下要求。

## 我的设计需求（请按此实现）
- 书名：【例如：简悦阅读笔记 2025】
- 副标题（可选）：【例如：技术文章精选】
- 卷号/册别（可选）：【例如：第一卷】
- 整体风格：【例如：深色极简、左侧色条、少量几何装饰；或：浅色文艺、底部渐变】
- 主色：【例如：#1a1a2e 背景 + #e8e4d9 文字】
- 强调色（可选）：【例如：#c9a227】
- 是否需要预留背景图区域：【是/否；若是，用占位说明，我稍后替换为本地文件 covers/bg.png】

## 技术与输出格式（必须遵守）
1. 只输出一个完整 HTML 文件内容（内联 `<style>` 即可），不要解释文字，不要 markdown 代码块包裹以外的废话。
2. 页面为 **A4 竖版**（210mm × 297mm），单页封面，无滚动第二页。
3. 必须使用打印 CSS：
   - `@page { size: A4; margin: 0; }`
   - 根容器精确占满一页（用 mm，例如 width: 210mm; min-height: 297mm;）
   - `@media print` 中设置 `print-color-adjust: exact` 和 `-webkit-print-color-adjust: exact`
4. **所有可见文字必须是 HTML 文本**（h1、p 等），禁止用图片代替标题；禁止在 CSS 里用 content 生成大段正文。
5. **禁止**使用任何外链资源（无 Google Fonts、无 https 图片、无 CDN）。中文字体使用：`font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;`
6. 若需要背景图，只用相对路径占位：`background-image: url("bg.png");`，并注释说明我将把 bg.png 与 html 放在同一目录。若暂无图，用纯色/渐变即可。
7. 为便于我修改，请使用语义化 class，至少包含：
   - `.cover-page`（整页容器）
   - `.book-title`（书名，最醒目）
   - `.book-subtitle`（副标题，可选）
   - `.book-volume`（卷号，可选）
   - `.cover-footer`（底部小字，可选，如年份、作者笔名）
8. 版式：书名居中或左对齐请按我的风格来；留出合理边距（建议四边不少于 15mm）；确保打印时不会被裁切重要文字。
9. 不要使用 JavaScript；不要依赖 flex/grid 在旧版打印引擎下失效的实验特性，优先稳妥布局（flex 可用但请测试打印友好）。
10. 在 HTML 顶部用 HTML 注释写 3 行「打印说明」：Chrome 打开 → 打印 → 纸张 A4 → 边距无 → 另存为 PDF。

## 输出后我会做的后续步骤（你无需实现）
- 浏览器微调 CSS
- 可选：添加本地 bg.png
- 打印为 PDF 后放入 sr_book 的 manifest cover_pdf

请直接生成完整 HTML。
