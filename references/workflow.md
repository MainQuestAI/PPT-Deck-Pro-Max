# Workflow

## 目标

把 Deck 生产固定成一条可复用流程，而不是一次性排版任务。

## 标准阶段

1. `deck_brief.md`
2. `deck_vibe_brief.md`
3. `deck_narrative_arc.md`
4. `deck_hero_pages.md`
5. `deck_layout_v1.md`
6. `deck_clean_pages.md`
7. `deck_visual_composition.md`
8. `deck_asset_plan.md`
9. `asset_manifest.json`
10. `deck_visual_system.md`
11. `deck_component_tokens.md`
12. `deck_theme_tokens.json`
13. `deck_geometry_rules.md`
14. `deck_page_skeletons.md`
15. `slide_state.json`
16. 成品 deck
17. `deck_review_report.md`
18. `layout_manifest.json`（如构建路径支持）
19. `review_package.json`
20. `deck_review_findings.json`
21. `commercial_scorecard.json`
22. `review_rollback_plan.json`
23. `review_rollback_plan.md`

## 推荐命令入口

优先使用总控脚本：

```bash
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages <n> --output-mode pptx+html
python3 scripts/run_deck_pipeline.py build-context --project-dir <project-dir> --page-ids slide_01
python3 scripts/run_deck_pipeline.py stage --project-dir <project-dir> --global-status building
python3 scripts/run_deck_pipeline.py manifest --project-dir <project-dir> --merge-existing
python3 scripts/run_deck_pipeline.py extract-layout --project-dir <project-dir>
python3 scripts/run_deck_pipeline.py review-package --project-dir <project-dir>
python3 scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role review
python3 scripts/run_deck_pipeline.py qa --project-dir <project-dir> --write-state --require-review --require-commercial-scorecard --require-layout-manifest --review-findings <project-dir>/deck_review_findings.json --commercial-scorecard <project-dir>/commercial_scorecard.json
python3 scripts/run_deck_pipeline.py route-review --project-dir <project-dir> --write-state
python3 scripts/run_deck_pipeline.py rework-handoff --project-dir <project-dir> --role visual
python3 scripts/run_deck_pipeline.py validate --project-dir <project-dir> --output-mode pptx+html
```

这样可以减少手工拼接多个脚本调用时的错误率。

正式评审版建议在 QA 与 validate 阶段同时打开 review、commercial scorecard、layout manifest 相关门禁。

## 常用快捷入口

### 方案型 Deck

```bash
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages 12 --preset solution_deck
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages 12 --preset internal_strategy
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages 12 --preset industry_pov
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages 12 --preset business_partnership
python3 scripts/run_deck_pipeline.py preset --project-dir <project-dir> --preset solution_deck
```

### 产品介绍型 Deck

```bash
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages 10 --preset product_intro
python3 scripts/run_deck_pipeline.py preset --project-dir <project-dir> --preset product_intro
```

### 给 AI 员工发任务

```bash
python3 scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role brief
python3 scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role visual
python3 scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role build --page-ids slide_05
python3 scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role review
```

### 生成几何 manifest

```bash
python3 scripts/run_deck_pipeline.py manifest --project-dir <project-dir> --merge-existing
```

当构建链路还不能原生吐出几何元数据时，先用这条命令生成 `layout_manifest.json` 骨架，再让 Build AI 或后处理脚本逐页补实。

### 从真实 PPTX 抽几何

```bash
python3 scripts/run_deck_pipeline.py extract-layout --project-dir <project-dir>
```

这一步会从已经生成的 `.pptx` 里抽取更真实的页级几何信息，优先用于正式 QA。

### 评审与返工

```bash
python3 scripts/run_deck_pipeline.py review-package --project-dir <project-dir>
python3 scripts/run_deck_pipeline.py qa --project-dir <project-dir> --extract-layout-from-pptx --require-review --require-commercial-scorecard --require-layout-manifest --review-findings <project-dir>/deck_review_findings.json --commercial-scorecard <project-dir>/commercial_scorecard.json --write-state
python3 scripts/run_deck_pipeline.py route-review --project-dir <project-dir> --write-state
python3 scripts/run_deck_pipeline.py rework-handoff --project-dir <project-dir> --role visual
python3 scripts/run_deck_pipeline.py validate --project-dir <project-dir> --formal --expert-mode --output-mode pptx+html
python3 scripts/run_deck_pipeline.py validate-schema --project-dir <project-dir> --strict
```

## 阶段门槛

### Gate 1：Brief 锁定

必须回答：

- 卖什么
- 卖给谁
- 最终 CTA 是什么
- 生产模式：expert（默认）还是 quick

### Gate 1.5：Expert Interview 完成（expert mode only）

- Hero claims 的 gap fill rate ≥ 80%
- 所有 insights 已确认或标记 skipped
- interview_session.json 状态为 completed 或 aborted（带已收集的 insights）

### Gate 1.6：Redaction Review 通过（expert mode only）

- 所有 needs_redaction 项已处理（clear / redacted / removed）
- deck_expert_context.md 已生成（干净的最终产物）
- brief_feedback 已呈现给用户（如有）

### Gate 2：Vibe 锁定

必须回答：

- 这套 Deck 长什么样
- 哪些页是重视觉，哪些页是重分析

### Gate 3：叙事弧线 + Hero Pages 锁定

必须回答：

- 每页归属什么 beat（setup / tension / resolution / proof / action）
- 信心拐点在第几页
- 哪些页是呼吸页
- 前 3 页是否建立了紧迫感或识别感

至少锁 3 到 5 页决定成败的页面，且 hero page 选择必须与 beat 类型对齐。

### Gate 4：Clean Pages + Visual Composition + Asset Plan 完成

出图 AI 只吃纯净逐页稿和视觉施工图，不吃长文档。
每页必须有视觉主角定义（`deck_visual_composition.md`）。
proof beat 和 hero 页应完成配图需求梳理（`deck_asset_plan.md`），用户已确认获取方式。

### Gate 5：Visual System 锁定

出图前必须锁组件、token、图表规则。

### Gate 6：Geometry 锁定

出图前必须锁定：

- 页面主区块边界
- 主视觉占比
- 关键元素对齐轴
- 连线或连接关系的几何规则
- archetype 的密度上下限

### Gate 7：Build

完成成品并产出页级 PNG / montage。

### Gate 8：Review + QA

先产出 `review_package.json`，再跑多模态 Review。

建议要求：

- 如果是正式评审版，`qa` 默认应使用 `--require-review`
- 如果是正式评审版，建议同时使用 `--require-commercial-scorecard`
- 如果是默认 `expert` 模式，`qa` 报告必须显式输出 `Expert Mode Gate`
- 如果 `review_package.json` 或运行时 summary 显示 expert gate 未闭环，QA 应直接失败，而不是只做提示
- 没有 `deck_review_findings.json`，不应直接标记为 `ready`
- 没有 `commercial_scorecard.json`，不应直接标记为 `ready`
- 有 `deck_review_findings.json` 时，应自动产出 `review_rollback_plan.json/.md`
- 返工时优先按 rollback plan 把问题分派给 `brief / visual / build`，而不是直接在成品页上盲修
- 如需把返工任务直接拆给 AI 员工，使用 `rework-handoff` 生成按角色过滤的返工指令

状态更新建议：

- 每个关键阶段完成后，用 `scripts/update_slide_state.py` 更新全局或页级状态
- 生成 rollback plan 后，把页面级回退层、回退目标文件和回退原因写回 `slide_state.json`
