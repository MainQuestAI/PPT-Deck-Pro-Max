# Expert Interview Guide

## 目标

引出专家脑中的隐性知识——具体案例、真实数据、因果判断、具象类比、异议回应——让 Deck 的内容从"正确但泛"变成"精准且有说服力"。

**核心原则：AI 不是采访机器，是带着自己判断的共创者。先说自己的理解，再请专家修正。**

## 适用条件

Expert Interview 在 `production_mode: expert` 时执行（默认模式）。Quick Mode 跳过此步。

## 运行时对象的生命周期

### Gap 是过程对象，Claim 是持久对象

```
1. AI 分析原稿 → 提取初始 claims（原稿已有的论点）
2. AI 对每条 claim 检查 5 种缺口 → 生成 gaps
3. Expert Interview 填补 gaps → 产出 insights
4. Insights 归入已有 claim 或触发新建 claim
5. Gap 标记为 filled 或 skipped
6. Interview 结束后：gaps 消亡，claims + insights 持久化
```

### 脚本 vs AI 的职责分工

**`generate_interview_questions.py` 做规则化的事：**
- 从原稿按页切片提取初始 claims
- 对每条 claim 用规则检查 5 种 gap（有没有具体名词？有没有因果连接词？有没有数字？）
- 计算每条 claim 的 richness_score
- 输出 gap 清单 + 按优先级排序

**AI 在运行时做理解力的事：**
- 读取 gap 清单和原稿上下文
- 基于对业务的理解形成假设
- 构造"我的判断是 X，你觉得对吗？"的带假设问题
- 引导对话、确认理解、处理意外回答

## 五种缺口的识别

### 规则化检测（脚本执行）

| 缺口类型 | 检测规则 | 信号 |
|---------|---------|------|
| **case** | claim 文本中没有具体企业名、产品名、"例如/比如/案例" | 缺少具象的客户/场景 |
| **causal** | claim 文本中没有"因为/所以/根源/导致/本质上" | 结论是并列的，没分主次 |
| **data** | claim 文本中没有数字、百分比、"率/量/额/倍" | 无可量化的锚点 |
| **contrast** | claim 有对比但没有"像/类似/就像/好比" | 差异化是抽象的 |
| **objection** | claim 涉及 Brief 中定义的关键顾虑相关主题 | 可能被质疑但没预防 |

### AI 运行时的提问方向

| 缺口 | 提问方向 | 示例 |
|------|---------|------|
| case | "你见过的客户里，哪个最能说明这个问题？" | → "XX 品牌 2000 万会员只用 12 个包" |
| causal | "这几个问题之间有没有主次？如果只解决一个，先解决哪个？" | → "认知层是根因" |
| data | "用一个数字证明问题有多严重，你会用什么？" | → "活跃人群包 < 1%" |
| contrast | "你怎么跟客户解释新旧方式的区别？有没有一个比喻？" | → "金牌导购 vs 自动发券机" |
| objection | "客户在这个点上最常反驳什么？你通常怎么回应？" | → "不是浪费，是地基" |

## 反偏置机制

### 确认偏误的风险

AI 先说假设，专家容易顺着说。这会强化 AI 的先验而不是纠正它。

### 规则

- 每 3-4 个问题中，至少 1 个是反证/挑战型
- 不在第一个问题就反证（先建立共识再挑战）
- 反证格式：`"如果 [AI 假设] 是错的，最可能错在哪里？"`
- 如果专家推翻 AI 假设，AI 必须显式更新理解并确认
- 反证结果如果改变 claim 核心主张，标记 `claim_revised=true`

### 示例

```
正常问题（问题 1-2）：
  "我的判断是认知层最根本。你在客户面前，哪一层最让他们点头？"

反证问题（问题 3）：
  "如果认知层不是根因呢？有没有客户觉得决策层或内容层才是核心瓶颈的情况？"
```

## Coverage 驱动的对话节奏

### 不用轮次硬编码，用 gap 填补率

**目标：hero claims 的 gap fill rate ≥ 80%**

- fill rate < 50% → 继续问最关键的 topic
- fill rate 50-80% → 问次优先 topic，每个更简短
- fill rate ≥ 80% → AI 提议："核心话题基本覆盖了，还有 N 个次要话题。要继续还是够了？"
- 超时（≥ 20 分钟）→ 自动收尾

### 优先级排序

1. Hero claims（hero_cover, hero_proof, hero_system, hero_cta 相关）
2. richness_score 最低的 claims
3. 有 case 或 data gap 的 claims（这两种对说服力影响最大）
4. 有 objection gap 的 claims（Brief 中的关键顾虑相关）

## Richness Score 计算

每条 claim 自动计算：

| 维度 | +1 条件 |
|------|--------|
| 案例 | 有 `insight_type=case` 的 expert insight |
| 因果 | 有 `insight_type=causal` 或 `claim_type=causal_judgment` |
| 数据 | 有 `level=expert_confirmed` 或 `factual` 的 evidence |
| 类比 | 有 `insight_type=analogy` |
| 异议 | 有 `insight_type=objection_response` |

- 满分 5
- Compression 时 richness < 2 标记 `needs_enrichment`
- QA 时 hero claim richness < 3 触发 `content_thin` finding

## 脱敏规则

### 实时识别

AI 在对话中识别敏感信息，立即标记 `needs_redaction`：
- 具体企业名称（非公开信息语境下）
- 人名
- "内部数据/不能对外/保密"相关表述
- 具体金额、合同数字、预算

### 默认安全

- 行业通用表述（"头部品牌普遍…"）
- 已脱敏表述（"某品牌"）
- 公开数据（财报、政府统计）

### 审批时机

Step 1.6（Redaction Review）集中处理。Compression 只读审批通过后的最终产物。

## Brief Feedback

Interview 中如果发现 Brief 不准确，不自动修改。在 `deck_expert_context.md` 中记录 `brief_feedback`，用户在 Step 1.6 审批时决定是否更新 Brief。
