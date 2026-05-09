# Deck Production Orchestrator

> 把商业 Brief 变成产品级演示文稿——不是普通的 AI PPT。

一套 AI Skill，编排商业演示文稿的完整生产周期：从商业 Brief 到叙事弧线、视觉组合设计、页面构建，再到结构化 QA 与回退路由。

**这不是构建引擎。** 它是坐在构建工具（如 Anthropic 的 `$slides` / `$frontend-design`，或任何 PPTX/HTML 生成工具）之上的编排层，确保产出物在商业上可用、视觉上丰富、叙事上连贯。

## 为什么不一样

多数 AI PPT 工具把文档转成幻灯片。这个 Skill 把演示文稿的制作当作一套**视觉沟通生产系统**——有阶段门槛、角色隔离和质量控制。

| 能力 | 普通 AI PPT | Manus 类图片生成 | 本 Skill |
|------|-----------|--------------|---------|
| 工作流 | 一次生成 | 一次生成 | 8 步强制流水线 + 门槛 |
| 内容密度 | 太稀或太密 | 压缩 | **文档模式默认**（250-350 字/页，独立可读） |
| 视觉设计 | 文字塞进方框 | AI 生成图片 | **逐页视觉组合规格**（图表类型、icon、数据可视化、布局） |
| 叙事 | 无 | 无 | Beat 弧线（setup/tension/resolution/proof/action） |
| 证据 | 截图或空白 | 概念模型 | **配图管线**（自动截图、设备壳、概念化 UI 骨架） |
| 内容丰富度 | 原稿有什么就有什么 | 压缩 | **Expert Mode** — AI 和专家对话，引出案例、数据、因果链 |
| 多 Agent | 单模型 | 单模型 | 5 个隔离角色（Brief / Visual / Build / Review / **Expert Interviewer**） |
| QA | 手动 | 无 | 25+ 自动检测项、商业评分、世界观闭合度 |
| 失败时 | 重来 | 重来 | **结构化回退**——路由到正确的上游阶段和角色 |
| 可编辑性 | 各异 | 扁平图片 | 真实 shape 的 PPTX / HTML |

## 核心设计哲学

**Skill 用"视觉组合"思维而非"文字结构"思维。**

每一页都有视觉主角（图表、icon 链、仪表盘、架构图、概念化 UI），不只是文字面板。压缩步骤不是"把文字缩短"，而是"把商业逻辑翻译成视觉沟通规格"。

**80% 的商业 Deck 是被"看"的，不是被"讲"的。** 文档模式为默认。每一页必须在没有演讲者的情况下自行解释清楚。

**内容丰富度来自专家，不来自 AI 推断。** v2.0 引入 Expert Mode：AI 分析原稿，识别 5 种知识缺口（案例、因果、数据、对比、异议），然后与领域专家进行结构化对话。结果是真实的案例、真实的数字、真实的因果判断——不是 AI 推断的近似值。

**世界观闭合度 > 视觉打磨度。** 读者翻完整套 Deck 后应该觉得"这个系统已经存在了"，而不是"这只是一个方案建议"。禁止空占位符，用概念化 UI 骨架替代。

**内部语言不得泄露。** 编排层的术语（hero page、proof beat、CTA、objection handling）绝不出现在客户可见的标题、正文和 insight bar 中。每句文案必须经得起"截图转发给同事"的测试。

## 快速开始

```bash
# 先检查本地环境健康度
python3 scripts/run_deck_pipeline.py doctor

# 初始化一套 12 页的方案型 Deck
python3 scripts/run_deck_pipeline.py init \
  --project-dir ./my-deck --pages 12 --preset solution_deck --production-mode expert

# Quick Mode：适合小型、低风险 Deck
python3 scripts/run_deck_pipeline.py init \
  --project-dir ./quick-deck --pages 6 --preset product_intro --production-mode quick

# Expert Mode（v2.0）：提取 claims + gaps，准备专家访谈
python3 scripts/run_deck_pipeline.py expert-interview \
  --project-dir ./my-deck

# Expert Mode：脱敏审批通过后，生成 deck_expert_context.md
python3 scripts/run_deck_pipeline.py finalize-interview \
  --project-dir ./my-deck

# 生成视觉组合规格（逐页图表/icon/数据决策）
python3 scripts/run_deck_pipeline.py visual-composition \
  --project-dir ./my-deck

# 为 Build AI 生成交接 prompt
python scripts/run_deck_pipeline.py handoff \
  --project-dir ./my-deck --role build --page-ids slide_05

# 为首批关键页生成 batch handoff（自动从 image_build_jobs.json 取页）
python scripts/run_deck_pipeline.py handoff \
  --project-dir ./my-deck --role build --batch-id batch_01

# 为 batch 生成可直接分发给 subagent 的任务包
python scripts/run_deck_pipeline.py dispatch-build \
  --project-dir ./my-deck --batch-id batch_01

# 人审确认某张图通过后，统一回写 asset / job / batch 状态
python scripts/run_deck_pipeline.py asset-status \
  --project-dir ./my-deck --asset-id slide_03_screenshot --status approved \
  --final-path generated/slide_03_selected.png --clear-stale

# 当整批关键页都批准后，生成 HTML 装配包
python scripts/run_deck_pipeline.py prepare-assemble \
  --project-dir ./my-deck --batch-id batch_01

# 把 assemble_context 真实装配进 starter/index.html
python scripts/run_deck_pipeline.py assemble-html \
  --project-dir ./my-deck --batch-id batch_01

# HTML 装配完成后，统一把本批切到 embedded / awaiting_review
python scripts/run_deck_pipeline.py finalize-assemble \
  --project-dir ./my-deck --batch-id batch_01

# 或者一条命令直接收口：finalize -> screenshot -> review package -> QA
python scripts/run_deck_pipeline.py post-assemble-qa \
  --project-dir ./my-deck --batch-id batch_01

# 规划配图（识别哪些页需要截图）
python scripts/run_deck_pipeline.py asset-plan \
  --project-dir ./my-deck

# 从 URL 自动截图（需要 Playwright）
python scripts/run_deck_pipeline.py capture-assets \
  --project-dir ./my-deck --cookies cookies.json

# 套设备壳
python scripts/run_deck_pipeline.py apply-mockups \
  --project-dir ./my-deck

# 运行 QA（正式评审模式）
python scripts/run_deck_pipeline.py qa \
  --project-dir ./my-deck --write-state \
  --require-review --review-findings ./my-deck/deck_review_findings.json

# 验收所有产出物（正式评审）
python scripts/run_deck_pipeline.py validate \
  --project-dir ./my-deck --output-mode pptx+html --formal
```

## 强制工作流

```
Step 0     分类任务
Step 1     锁定 Brief                        → deck_brief.md            🔔 用户确认
Step 1.5 ★ Expert Interview（专家模式）       → interview_preparation.json
Step 1.6 ★ Redaction Review（脱敏审批）       → deck_expert_context.md   🔔 用户确认
Step 2     锁定 Vibe                         → deck_vibe_brief.md
Step 3     叙事弧线 + Hero Pages              → deck_narrative_arc.md    🔔 用户确认
Step 4     版式草稿                           → deck_layout_v1.md
Step 5     内容压缩 + 视觉组合设计             → deck_clean_pages.md
                                              → deck_visual_composition.md（逐页视觉规格）
Step 5.5   配图规划                           → deck_asset_plan.md       🔔 用户确认
Step 6     视觉组件系统                       → tokens、geometry、skeletons
Step 7     构建 Deck                          → .pptx / .html
Step 8     QA 与评审循环                      → findings、评分卡、回退计划
```

★ 标记的步骤仅 Expert Mode（默认）执行。在 Brief 中设置 `production_mode: quick` 可跳过。每一步都有门槛。不锁 Brief 不能进构建。不通过 QA 不能标记完成。QA 失败时，系统把问题路由到正确的上游阶段和角色——不是"从头来过"。

## 视觉组合层（v1.0+）

核心差异化。在内容压缩和构建之间，每一页获得一份**视觉施工规格**：

```markdown
## 第 3 页 — 三层断裂

### 视觉主角
类型：gauge_chart × 3
位置：每栏底部，占页面 30%

### 说明性数据
指标：深层意图理解率 | value=28% | gauge | illustrative=true
指标：策略动态调整率 | value=21% | gauge | illustrative=true

### Icon 指定
brain → 认知层断裂 | settings → 决策层断裂 | file-text → 内容层断裂

### 概念化 UI（截图不可用时）
类型：concept_ui | 标题：Fracture diagnostic console | 风格：terminal_window
```

Build AI 把这份规格作为一等输入——不是"三张诊断卡"四个字，而是精确的图表类型、数据值、icon 和布局比例。

## Expert Mode（v2.0）

AI 生成的 Deck 最大的差距不在视觉设计——而在**内容丰富度**。AI 能压缩原稿里的内容，但无法凭空创造真实的客户案例、真实的数据点和真实的因果判断。

Expert Mode 在 Brief 和叙事弧线之间增加了一步结构化对话：

1. **AI 分析**原稿，提取 claims（每页一个或多个独立论点）
2. **AI 检测 5 种缺口**：案例（case）、因果（causal）、数据（data）、对比（contrast）、异议（objection）
3. **AI 带假设提问**——不是"你有什么补充"，而是"我的判断是 X，你觉得对吗？"
4. **反偏置内建**：每 3-4 个问题至少 1 个反证问题
5. **Coverage 驱动**：目标是 hero claims 的 gap fill rate >= 80%，不是固定轮次
6. **脱敏门槛**：敏感信息被标记，在进入下游前独立审批

产出物是 `deck_expert_context.md`——结构化的专家知识绑定到语义 claims，不绑页号。Compression 合并时优先级：专家案例 > AI 概括，专家数字 > AI 推断值。

在 Brief 中设置 `production_mode: quick` 可跳过 Expert Mode（等同 v1.x 行为）。

## 角色隔离

五个 AI 角色，各自有严格的上下文可见性控制：

| 角色 | 可见 | 不可见 |
|------|------|-------|
| **Brief AI** | 原始商业材料、叙事弧线 | 实现代码、视觉补丁 |
| **Expert Interviewer AI** | Brief、claims、gaps、原稿 | 构建代码、视觉系统 |
| **Visual AI** | Brief、vibe、clean pages | 原始长文档、评审对话 |
| **Build AI** | 当前页切片、**视觉组合**、**expert context**、tokens | 其他页代码、原始文档 |
| **Review AI** | 产出物、montage、状态、评分卡 schema、**专家产物** | 预设答案、主观结论 |

## 配图管线

真实的产品截图让证据页的说服力提升 10 倍。配图管线处理完整流程：

1. **规划** — AI 扫描 clean pages，识别哪些页需要截图
2. **采集** — Playwright 自动截图，支持 cookie 登录态
3. **设备壳** — Pillow 渲染设备外壳（MacBook、浏览器、iPhone、平板、终端）
4. **占位** — 截图不可用时，品牌色占位符或**概念化 UI 骨架**维持世界观闭合度
5. **QA** — 证据页缺少真实素材会被报 `asset_missing` finding

## 项目结构

```
SKILL.md                         主指令文件（"大脑"）
references/                      33 份设计指引 + JSON Schema
  expert_interview_guide.md      5 种缺口识别 + 反偏置 + coverage 驱动
  title_writing_guide.md         判断句、30 字、2 行上限
  cta_design_guide.md            门槛控制 + 交付物承诺 + 紧迫感
  information_design_guide.md    数据关系 → 视觉形式映射（8 种）
  visual_composition_guide.md    如何生成逐页视觉规格
  concept_ui_guide.md            概念化 UI 骨架（世界观闭合度）
  illustrative_data_guide.md     5 级证据来源体系（expert > factual > inferred）
  compression_rules.md           文档模式 + 6 层丰富度模型 + 受众适配
  narrative_arc_guide.md         Beat 类型、弧线模板、情绪曲线
  commercial_scorecard.md        商业说服力评分（6 维度）
  build_contract.md              HTML/PPTX 组装合同
  ...另有 22 份
scripts/                         30 个 Python 脚本
  run_deck_pipeline.py           统一 CLI（17 个子命令）
  generate_interview_questions.py Claim 提取 + 5 种 gap 检测 + richness 评分
  finalize_interview.py          Step 1.6 执行器 — session 校验 + expert context 生成
  generate_visual_composition.py 逐页视觉规格生成器
  capture_assets.py              Playwright 截图采集
  apply_mockup.py                设备壳渲染（5 种框架）
  route_review_findings.py       结构化回退路由
  build_montage_and_report.py    QA 引擎（含 expert-mode 检测）
  ...另有 22 个
assets/
  chart_templates/               6 个可复用 HTML 图表模板
  mockup_frames/                 5 种设备壳规格
  presets/                       5 个商业场景预设
  theme_tokens/                  暗色玻璃 + 浅色纸张两套主题
  example_project/               10 页参考项目（含完整中间产物）
  fonts/                         Google Fonts 加载
tests/                           78 个测试（单元 + 集成 + 端到端）
.github/workflows/ci.yml        Python 3.10/3.11/3.12 CI
```

## 安装依赖

```bash
python3 -m pip install -r requirements.txt

# 本地测试依赖
python3 -m pip install -r requirements-dev.txt
```

- **Python 3.10+**
- `python-pptx` — PPTX 几何抽取
- `Pillow` — Montage 生成 + 设备壳渲染
- `jsonschema` — 运行时合同校验
- `playwright`（可选）— 自动截图 + 页级视觉 QA

安装后建议先跑健康检查：

```bash
python3 scripts/run_deck_pipeline.py doctor
python3 scripts/run_deck_pipeline.py doctor --project-dir ./my-deck
```

## 模式与最小样例

`--production-mode expert` 适合高价值商业 Deck：需要专家访谈、脱敏门槛和更完整的商业证据。`--production-mode quick` 适合小型 Deck 或快速验证，跳过 Expert Interview 的启动成本。

最小 smoke test：

```bash
./examples/solution_deck_minimal/run_smoke.sh
```

多 AI 员工协作时，使用 [AI Worker Execution Guide](docs/ai_worker_execution.md) 作为执行说明。

## 预设

| 预设 | 默认成交任务 | 弧线模板 |
|------|-----------|---------|
| `solution_deck` | 争取 Sponsor | setup → tension → resolution → proof → action |
| `product_intro` | 争取 Sponsor | setup → proof → resolution → tension → action |
| `internal_strategy` | 争取 Owner | tension → resolution → proof → action |
| `industry_pov` | 争取 Sponsor | tension → setup → resolution → proof → action |
| `business_partnership` | 争取 Sponsor | setup → resolution → proof → tension → action |

## QA 维度

QA 引擎在 9 大类下检查 25+ 项：

- **密度** — 文字溢出、文档模式下限（150 字）、hero 页阈值
- **组件漂移** — 未定义的视觉组件
- **几何稳定性** — 中心偏移、连线断裂、占比
- **演讲备注** — hero 页必须有演讲备注
- **配图** — 证据页必须有截图或概念化 UI
- **视觉平坦** — 缺少视觉主角的页面
- **世界观闭合度** — 翻完后是否觉得"系统已存在"
- **内部语言泄露** — 编排术语是否混入了客户可见文案
- **Expert Mode** — content_thin（hero richness < 3）、expert_data_ignored、redaction_incomplete
- **商业评分** — 6 维说服力评分卡 + 最低阈值
- **叙事** — 弧线连贯性、节奏单调、过渡缺失

## 推荐的 Build Skill 组合

本 Skill 是编排层，需要配合 Build Skill 使用。经过实战验证的组合：

| 组合 | 产出格式 | 视觉精细度 | 适用场景 |
|------|---------|----------|---------|
| `imagegen` + `frontend-design` | HTML / 图片型 PPT | 最高 | Codex 环境下推荐：先生成主视觉、mockup、概念 UI，再组装页面 |
| `frontend-slides` | HTML | 高 | 最推荐——专为演示文稿设计 |
| `ui-ux-pro-max` + `frontend-design` | HTML | 最高 | 设计智能增强 + 高保真实现 |
| `officeCLI` | PPTX / Office 文件 | 高 | 最终交付必须保持 Microsoft Office 原生格式时，用于 Office 构建与自动化 |
| `openai-slides` | PPTX | 中 | 需要可编辑 PPTX 时 |

Codex 图片型 PPT 的默认节奏是：`generate-assets` / `dispatch-build` → `$imagegen` 生成当前 batch → `asset-status` 批准资产 → HTML/PPTX 组装 → QA。这一轮图片迭代用于先锁定关键页视觉方向，降低后续返工成本。

## 协议

[MIT](LICENSE)

---

由 [MainQuest AI](https://github.com/MainQuestAI) 构建。
