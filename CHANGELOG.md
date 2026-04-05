# Changelog

## 1.1.1 — 视觉沟通层的运行时集成收尾

### 4 个运行时断点修复
- **context_manager.py 注入 visual_composition**：新增 `--visual-composition` 参数，Build context 现在按页切片包含视觉施工图。`run_deck_pipeline.py build-context` 自动传入 `deck_visual_composition.md`。Build AI 不再需要"根据文字自行猜视觉"。
- **generate_visual_composition.py 升级到完整施工图**：每页输出补齐主角位置/占比、视觉重量分布、模板引用、强调方式、概念化 UI 声明。从"视觉建议"升级为"视觉施工图"。
- **validate_deck_outputs.py 纳入视觉层产物**：CORE_ARTIFACTS 新增 `deck_visual_composition.md`、`deck_asset_plan.md`、`asset_manifest.json`。正式验收合同与 v1.0 视觉沟通系统完全对齐。
- **validate 子命令暴露 formal 模式**：新增 `--formal` 别名，一键启用正式评审验收（等同 `--require-review`）。

## 1.1.0 — 从"方案 Deck"升级为"世界观闭合的 Category Deck"

### 三个底层假设变更

**压缩哲学**：默认从演讲模式（80 字/页）切换为**文档模式（250-350 字/页）**。80% 的商业 Deck 是被"看"的不是被"讲"的，每页必须独立可读、论据充分，不能只留结论句。

**占位策略**：**禁止空占位符（SCREENSHOT PLACEHOLDER）**。当截图不可用时，必须使用概念化 UI skeleton（仿产品控制台骨架）建立产品存在感。新增 `references/concept_ui_guide.md`。

**成交任务定义**：Brief 模板新增"成交任务"字段——**争取 Sponsor（默认）** vs 争取 Owner。默认 Sponsor 模式产出 Category Deck（构建完整世界观），Owner 模式产出 Solution Deck（逻辑严密可追问）。

### 新增规则
- **世界观闭合度检查**：QA checklist 新增 6 项，新增 `world_incomplete` finding 类型和回退路由
- **装饰克制规则**：背景装饰透明度 ≤ 12%，面积 ≤ 15%，不得与内容竞争注意力
- **标题行数约束**：标题最多 3 行
- Success Criteria 新增 `world-complete` 和 `self-explanatory` 为前两项

### 核心洞察来源
基于 Codex vs Manus 同输入对比的深层分析：差距不在视觉设计，在于说服模型——Manus 构建"未来已来"的闭合世界，Codex 构建"可被批准"的方案论证。市场 80% 场景需要前者。

## 1.0.0 — 从"内容生产系统"升级为"视觉沟通系统"

### 架构级变更
- Skill 的设计哲学从"文字思维做视觉产物"升级为"视觉思维做视觉产物"
- Step 5 从"Editorial Compression"重写为"Content Compression + Visual Composition Design"
- 新增核心产物 `deck_visual_composition.md` — 逐页视觉施工图，坐在 clean_pages 和 build 之间
- Build AI 角色从"排版工人"重新定义为"视觉施工员"

### 新增 Reference 文件
- `references/information_design_guide.md`：8 种数据关系 → 视觉形式的完整映射规则
- `references/visual_composition_guide.md`：如何从文字内容生成逐页视觉施工图
- `references/illustrative_data_guide.md`：何时/如何生成和标记说明性数据

### 新增脚本
- `scripts/generate_visual_composition.py`：分析 clean pages 内容的数据关系，自动提议视觉主角、图表类型、icon、说明性数据

### 修改的核心文件
- `SKILL.md`：Step 5 重写，Resources 列表新增三个 reference
- `references/compression_rules.md`：目标从"压缩文字"改为"翻译成视觉沟通规格"
- `references/prompt_templates.md`：Build AI prompt 完全重写为视觉施工员角色
- `references/qa_checklist.md`：新增"视觉主角检查"专项（7 项）
- `references/review_findings.schema.json`：新增 `visual_flat` 类型
- `references/review_rollback_map.json`：新增 `visual_flat` 路由（回退到 visual_composition）
- `references/workflow.md`：新增视觉组合阶段
- `scripts/run_deck_pipeline.py`：新增 `visual-composition` 子命令
- `scripts/generate_role_prompt.py`：Build AI handoff 重写
- `scripts/init_deck_project.py`：新增 `deck_visual_composition.md` 模板

## 0.9.1

### 工程可靠性
- Review 循环收敛：`slide_state.json` 新增 `review_iteration` 计数器；`route_review_findings.py` 支持 `--max-iterations`（默认 3）和 `--recurrence-threshold`（默认 3），超限自动 escalate 为 `manual_review`。
- Runtime schema 校验：新增 `scripts/validate_schema.py`，支持 `--project-dir` 批量校验和 `--file` 单文件校验。Pipeline 新增 `validate-schema` 子命令。
- 端到端集成测试：新增 `tests/test_pipeline_integration.py`（12 个测试），覆盖 init → preset → asset-plan → QA → convergence 全链路。
- GitHub Actions CI：新增 `.github/workflows/ci.yml`，Python 3.10/3.11/3.12 矩阵，语法检查 + JSON 校验 + pytest。

## 0.9.0

### Asset Pipeline — 产品截图采集与配图系统
- 新增 `> 配图:` 声明格式，在 `deck_clean_pages.md` 中声明配图需求。
- 新增 `scripts/generate_asset_plan.py`：AI 分析 clean pages 自动输出 `deck_asset_plan.md` + `asset_manifest.json`。
- 新增 `scripts/capture_assets.py`：Playwright 自动截图，支持 `--cookies` 导入登录态。
- 新增 `scripts/apply_mockup.py`：设备壳渲染（MacBook/Browser/iPhone/Tablet/Terminal），纯 Pillow 绘制。
- 新增 `scripts/generate_placeholders.py`：品牌色占位符生成。
- 新增 `assets/mockup_frames/mockup_spec.json`：5 种设备壳规格定义。
- 新增 `references/asset_pipeline_guide.md`：配图系统完整指引。
- 新增 `references/asset_manifest.schema.json`：资产清单 schema。
- SKILL.md 新增 Step 5.5: Plan Assets。
- Pipeline 新增 4 个子命令：`asset-plan`、`capture-assets`、`apply-mockups`、`generate-placeholders`。
- QA 新增 `detect_missing_assets()` 检查 proof 页配图缺失。
- `review_findings.schema.json` 新增 `asset_missing` 类型。
- `review_rollback_map.json` 新增 `asset_missing` 路由。
- Build context 自动包含 asset 引用。

### 页面截图自动化
- 新增 `scripts/screenshot_pages.py`：Playwright 逐页截图 HTML deck。

### Speaker Notes 交付
- 新增 `scripts/inject_speaker_notes.py`：向 PPTX 注入 speaker notes + 导出 `speaker_notes.json`。

### 字体配置
- 新增 `assets/fonts/fonts.css`：Google Fonts CDN 加载。
- 新增 `references/font_loading_guide.md`：HTML/PPTX 字体配置指引。
- HTML starter 引用 fonts.css，使用 CSS 变量引用字体。

### 构建合同
- 新增 `references/build_contract.md`：HTML/PPTX 多页组装规范、speaker notes 传递合同、asset 引用合同、输出命名约定。

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
