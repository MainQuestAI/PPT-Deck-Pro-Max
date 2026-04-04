# Changelog

## 0.8.0

### Narrative Arc System
- 新增 `references/narrative_arc_guide.md`：5 种 beat 类型、5 种弧线模板、情绪曲线验证标准。
- 新增 `references/pacing_rhythm_guide.md`：密度曲线、呼吸页定义、过渡逻辑格式。
- 新增 `references/objection_handling_guide.md`：5 类异议处理策略与 commercial scorecard 对照。
- SKILL.md Step 3 从 "Define Hero Pages" 升级为 "Define Narrative Arc & Hero Pages"。
- workflow.md Gate 3 扩展：要求锁定 beat 序列和信心拐点。
- 5 个 preset 新增 `narrative_template` 字段，`apply_deck_preset.py` 自动生成 `deck_narrative_arc.md`。
- 示例项目新增 `deck_narrative_arc.md`。

### Speaker Notes System
- `deck_clean_pages.md` 格式扩展：hero pages 必须附带 `> 演讲备注:` 区块。
- `page_parser.py` 新增 `extract_speaker_notes()` 函数。
- `build_montage_and_report.py` QA 新增 hero page 演讲备注缺失检查。
- `context_manager.py` build context 包含 speaker notes。

### Narrative QA
- `review_findings.schema.json` 新增 4 种类型：`narrative_broken`、`pacing_monotone`、`transition_missing`、`speaker_notes_missing`。
- `review_rollback_map.json` 新增 4 条路由规则。
- `qa_checklist.md` 新增叙事与节奏检查专项（7 项）。
- `prompt_templates.md` 4 个角色更新：Brief AI 引用叙事弧线，Build AI 传递 speaker notes，Review AI 检查叙事和备注。

### Open Source
- 新增 `README.md`（中英双语，含快速开始、架构总览、目录结构）。
- 新增 `LICENSE`（MIT）。
- 新增 `requirements.txt`。

## 0.7.0

- 新增 `commercial_scorecard.json` 流程，把“能不能卖”纳入结构化评审。
- 新增 `generate_commercial_scorecard.py`、`update_layout_manifest.py` 与 `layout-update` 命令。
- 扩展 findings 类型，覆盖受众偏差、购买理由模糊、顾虑未回答、证据顺序错误、商业动作不清。
- QA 支持商业评分卡门槛与最低分校验。
- Build AI 现在可以回写真实页级几何数据到 `layout_manifest.json`。
- 补齐 `check_layout_stability.py`，把几何稳定性从口头标准升级成可执行 QA。
- 新增 `generate_layout_manifest.py` 与 `manifest` 命令，支持从 `slide_state + skeletons` 生成/刷新 `layout_manifest.json`。
- `generate_review_package.py` 改为通用产物发现逻辑，不再写死客户项目文件名。
- 新增浅色主题 `default_light_paper.json`。
- 预设扩充到 `internal_strategy / industry_pov / business_partnership`。
- 新增 chart templates：`stage_band / priority_stack / diagnostic_board`。
- 新增 `slide_state.schema.json / layout_manifest.schema.json / review_rollback_plan.schema.json`。
- 增加单元测试覆盖 `page_parser / apply_deck_preset / route_review_findings / layout_stability`。

## 0.5.0

- 新增 `rework-handoff`，支持按角色拆分返工任务。
- 新增结构化 review gate 与 `review_package.json`。

## 0.4.0

- 新增 `run_deck_pipeline.py` 统一编排入口。
- 新增图表模板渲染器 `render_chart_template.py`。
