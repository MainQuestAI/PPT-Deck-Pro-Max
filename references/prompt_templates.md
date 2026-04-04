# Prompt Templates

## Brief AI

输入：
- 原始业务需求
- 长文档或会议纪要

任务：
`请基于这份原始材料，输出 deck_brief.md。必须锁定产品主语、产品定位、目标受众、第一购买理由、最强差异化、最强证据、首单入口和最终 CTA。不要写视觉内容，不要进入逐页结构。`

输出约束：
- 只写 Brief
- 用业务语言
- 不写技术实现
- 不写风格语言
- 如果 `deck_narrative_arc.md` 已存在，后续页面文稿必须尊重 beat 序列和过渡逻辑
- hero pages 的 clean pages 必须附带 `> 演讲备注:` 区块
- proof beat 和 hero 页应使用 `> 配图:` 声明所需的产品截图（参见 `references/asset_pipeline_guide.md`）
- 如果需要补充后续页面文稿约束，统一要求 `deck_clean_pages.md` 使用 `## 第 N 页` 作为分页符
- 如果处于返工期，优先接收按角色过滤后的 rework handoff，不要自行扫描完整 rollback plan

## Visual System AI

输入：
- `deck_brief.md`
- `deck_vibe_brief.md`
- `deck_hero_pages.md`
- `deck_clean_pages.md`
- `review_rollback_plan.md`（如果存在）

任务：
`请输出 deck_visual_system.md、deck_component_tokens.md 和 deck_theme_tokens.json。你负责锁视觉世界观、组件系统和 token，不要重写业务主线。`

输出约束：
- 组件必须可复用
- 页面原型数量有限
- 不得引入野生风格
- 不改写 `deck_clean_pages.md` 的分页规则；分页统一使用 `## 第 N 页`
- 如果处于返工期，优先只处理分配给 `visual` 的 rollback 项

## Build AI

输入：
- 当前页 `deck_clean_pages` 切片
- `deck_visual_system.md`
- `deck_component_tokens.md`
- `deck_theme_tokens.json`
- `slide_state.json`
- `review_rollback_plan.md` 中与当前页相关的返工项（如果存在）

任务：
`请只生成当前这一页。不要引用其他页面的实现代码，也不要补看原始长文档。若需要图表，优先复用 assets/chart_templates/ 下的模板并替换占位符。`

输出约束：
- 一页一个主角
- 不引入未定义组件
- 不做额外解释
- 只输出当前页需要的实现
- 如果 clean pages 包含 `> 演讲备注:`，必须传递到成品（pptx 的 speaker notes 或 html 的注释）
- 如果 build context 包含 `assets` 字段，按路径引用图片嵌入到页面的指定位置
- 如果需要回补或修正 `deck_clean_pages.md`，必须保持 `## 第 N 页` 分页格式
- 如果处于返工期，只处理 build rework handoff 中列出的页面

## Review AI

输入：
- `review_package.json`
- 成品 deck
- 缩略总览
- `deck_clean_pages.md`
- `slide_state.json`
- `review_findings.schema.json`
- `commercial_scorecard.schema.json`

任务：
`请基于 review_package.json 先做多模态评审，再输出结构化 findings。优先指出会削弱商业说服力、证据强度、关键页主角性和视觉一致性的问题。`

输出建议：
- 输出为 `deck_review_findings.json`
- 必须符合 `review_findings.schema.json`
- 必须同时输出 `commercial_scorecard.json`
- 每条必须包含 `page_id`、`severity`、`type`、`reason`、`suggested_fix`、`source_image`
- 优先结合 `montage.png`、页级 PNG 或截图做多模态评审，再回看文字与状态文件
- 重点检查是否有普通 AI 味、视觉层级是否清晰、关键页是否失焦、是否偏离既定视觉系统
- 检查叙事弧线是否连贯：beat 序列是否合理、过渡逻辑是否成立、有无节奏单调
- 检查 hero pages 是否有演讲备注
- findings 会被系统自动映射成 `review_rollback_plan.json/.md`，所以 `type` 必须认真选择，不能滥用 `other`
