# Workflow

## 目标

把 Deck 生产固定成一条可复用流程，而不是一次性排版任务。

## 标准阶段

1. `deck_brief.md`
2. `deck_source_digest.md`
3. `deck_claim_map.json`
4. `deck_capacity_plan.md`
5. `deck_capacity_plan.json`
6. `deck_gap_registry.json`
7. `deck_question_queue.md`
8. `deck_section_packages.md`（longform）
9. `section_packages.json`（longform）
10. `deck_vibe_brief.md`
11. `deck_narrative_arc.md`
12. `deck_hero_pages.md`
13. `deck_layout_v1.md`
14. `deck_clean_pages.md`
15. `deck_visual_composition.md`
16. `deck_asset_plan.md`
17. `asset_manifest.json`
18. `deck_visual_system.md`
19. `deck_component_tokens.md`
20. `deck_theme_tokens.json`
21. `deck_geometry_rules.md`
22. `deck_page_skeletons.md`
23. `slide_state.json`
24. 成品 deck
25. `deck_review_report.md`
26. `layout_manifest.json`（如构建路径支持）
27. `review_package.json`
28. `deck_review_findings.json`
29. `commercial_scorecard.json`
30. `review_rollback_plan.json`
31. `review_rollback_plan.md`

## 生产子模式

默认子模式是 `standard_deck`，适合普通产品介绍、方案、战略、行业观点和合作 Deck。

当项目是正式投标、RFP、技术方案或留资型图片整页 Deck 时，使用 `formal_bid_image_led`。该子模式额外要求：

1. `page_registry.md`
2. `image_generation_manifest.md`
3. `actual_page_mapping.md`
4. `known_issue_log.md`

这些文件用于锁定源页面 ID、实际 PPT 页码、Go / No-Go 图片决策、已过线图片路径和已知问题闭环。

## 推荐命令入口

优先使用总控脚本：

```bash
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages <n> --output-mode pptx+html
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages <n> --output-mode pptx+html --production-sub-mode formal_bid_image_led
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
python3 scripts/run_deck_pipeline.py validate --project-dir <project-dir> --output-mode pptx+html --expert-mode --content-governance
python3 scripts/run_deck_pipeline.py validate --project-dir <project-dir> --output-mode pptx+html --expert-mode --longform-governance
python3 scripts/run_deck_pipeline.py section-handoff --project-dir <project-dir> --section-id section_01
python3 scripts/run_deck_pipeline.py validate --project-dir <project-dir> --output-mode pptx+html --production-sub-mode formal_bid_image_led
python3 scripts/run_deck_pipeline.py assemble-formal-images --project-dir <project-dir>
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
python3 scripts/run_deck_pipeline.py section-handoff --project-dir <project-dir> --section-id section_01
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
- 生产子模式：standard_deck 还是 formal_bid_image_led

### Gate 1.2：内容治理门禁（expert / longform）

必须回答：

- 原始资料里有哪些可用事实、证据、案例和明确缺口
- 当前资料能支撑多少核心页、证明页、扩展页
- `target_pages` 是否超过 `max_supported_pages`
- 哪些 gap 会阻塞逐页稿
- 进入 Expert Interview 前优先问哪些问题

必须产出：

- `deck_source_digest.md`
- `deck_claim_map.json`
- `deck_capacity_plan.md`
- `deck_capacity_plan.json`
- `deck_gap_registry.json`
- `deck_question_queue.md`

长篇 / expert deck 在进入逐页稿前必须通过：

```bash
python3 scripts/run_deck_pipeline.py validate \
  --project-dir <project-dir> --output-mode pptx+html \
  --expert-mode --content-governance
```

Quick mode 默认可跳过该门禁，除非用户主动要求内容治理。

### Gate 1.7：长篇治理门禁（longform）

适用于 expert + standard_deck + longform。formal_bid_image_led 暂时不强制接入该主链路。

必须回答：

- 四档页数预算分别能做多少页：conservative、recommended、extended、appendix_heavy
- 超过 recommended 后，需要补充哪些信息或转入哪些附录型内容
- 每个章节包的目标、页数配额、claim 归属和证据复用边界
- 哪些话题禁止在其他章节重复
- 每个高密度章节应使用哪个 dense archetype

必须产出：

- `deck_section_packages.md`
- `section_packages.json`
- `references/dense_page_archetypes.md`

长篇 deck 在进入分章节逐页稿前必须通过：

```bash
python3 scripts/run_deck_pipeline.py validate \
  --project-dir <project-dir> --output-mode pptx+html \
  --expert-mode --longform-governance
```

章节稿建议使用独立 handoff：

```bash
python3 scripts/run_deck_pipeline.py section-handoff \
  --project-dir <project-dir> --section-id section_01
```

每个章节交接包只包含该章节目标、页数配额、claim / gap 子集、允许证据、禁止重复话题、过渡要求和建议原型。主线程负责整本叙事、跨章节去重和最终合并。

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

### Gate 6.5：正式投标图片型页表锁定（formal_bid_image_led only）

必须先锁：

- 源页面 ID 与实际 PPT 页码映射
- 章节、页标题、逐页稿或源 prompt 路径
- 候选图、Go 图、No-Go 图和替换图状态
- 直接引用页、附录页或非计数章节造成的页码空洞
- 已知问题、修复 owner 和是否阻塞交付

没有 `page_registry.md` 和 `actual_page_mapping.md`，不进入批量生图或最终 PPT 装配。

### Gate 7：Build

完成成品并产出页级 PNG / montage。

Codex 图片型 PPT 增加一轮图片迭代：

- 先用 `generate-assets` / `dispatch-build` 形成当前 batch 的生图任务
- 当前运行环境是 Codex 时，优先调用 `$imagegen` 生成页面主视觉、产品 mockup、概念 UI 和纹理资产
- `$imagegen` 产物必须保存到项目目录，并通过 `asset-status` 回写 `asset_manifest.json` 与 `image_build_jobs.json`
- 首批 hero / proof / system 图片批准后，再进入 HTML/PPTX 组装

正式投标图片型 Deck 额外要求：

- 从 `page_registry.md` 生成或核对生图批次
- 候选结果保留在候选目录
- 只有 Go 页进入已过线目录
- 最终另建实际页目录，不覆盖源 ID 目录
- 使用 `assemble-formal-images` 按 `actual_page_mapping.md` 复制出最终装配目录，并在覆盖前保留备份

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
- 如果是 `formal_bid_image_led`，`validate` 必须检查页表、图片生成 manifest、实际页码映射和已知问题记录是否存在

状态更新建议：

- 每个关键阶段完成后，用 `scripts/update_slide_state.py` 更新全局或页级状态
- 生成 rollback plan 后，把页面级回退层、回退目标文件和回退原因写回 `slide_state.json`
