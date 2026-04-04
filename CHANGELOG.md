# Changelog

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
