# Narrative Arc Guide

## 目标

让 Deck 不是"信息罗列"，而是"说服旅程"。

每套商业 Deck 都应有一条清晰的叙事弧线：从建立识别到制造紧迫，从展示能力到提供证据，最终推动行动。

## Beat 类型

每一页应归入以下五种 beat 之一：

### setup

情绪目标：识别感、共鸣。
信息密度：低到中。
典型 archetype：hero_cover, context_board。
核心任务：让受众觉得"你知道我在面对什么"。

### tension

情绪目标：紧迫感、不安。
信息密度：中。
典型 archetype：diagnostic_board, comparison_board。
核心任务：把问题放大到不能忽略的程度。可以是现状诊断、竞争威胁或机会成本。

### resolution

情绪目标：清晰感、方向感。
信息密度：中到高。
典型 archetype：system_map, process_or_timeline。
核心任务：展示"怎么解决"和"为什么这么解决"。不是罗列功能，而是展示方法逻辑。

### proof

情绪目标：信心、可信度。
信息密度：中到高。
典型 archetype：proof_board, value_stack, comparison_board。
核心任务：用真实证据（数据、案例、样例页）建立可信度。

### action

情绪目标：动作感、低门槛。
信息密度：低。
典型 archetype：cta_board。
核心任务：让对方知道下一步该做什么，且觉得这一步很容易跨出。

## 典型弧线模板

### 方案型 Deck

```
setup → tension → tension → resolution → proof → proof → action
```

先建立共鸣，再制造两轮痛点压力，然后展示解决方案，用两轮证据收紧，最后推动行动。

### 产品介绍型 Deck

```
setup → proof → resolution → proof → tension → action
```

先让产品说话（样例页前置），再解释怎么做到的，用第二轮证据强化差异化，最后用错过代价制造紧迫。

### 内部战略汇报

```
tension → tension → resolution → resolution → proof → action
```

内部汇报不需要 setup，直接进入核心矛盾，用双层诊断建立紧迫性，双层解决方案锁定战略路径。

### 行业观点型 Deck

```
tension → setup → resolution → proof → proof → action
```

先用行业断裂制造震撼，再用 setup 页解释"为什么是现在"，然后展示新范式和证据。

### 商务合作提案

```
setup → resolution → proof → proof → tension → action
```

先让对方看到合作价值，快速展示合作机制和双方证据，最后用"不合作的代价"推动签约。

## 情绪曲线验证标准

一条合格的叙事弧线必须满足：

1. 前 3 页建立紧迫感或识别感（至少包含 1 个 tension 或 1 个 setup）
2. 中段存在信心拐点（从 tension/setup 到 resolution/proof 的转折）
3. 最后 2 页有明确的动作感（至少包含 1 个 action beat）
4. 不存在连续 3 页相同 beat 类型
5. tension 后不能直接跳到 action（必须经过 resolution 或 proof）

## 与 Hero Pages 的关系

beat 类型直接影响哪些页应该是 hero page：

- tension beat 的页通常是 hero，因为它决定了受众是否继续看下去
- proof beat 的页如果包含最强证据，应该是 hero
- action beat 的 CTA 页始终是 hero
- resolution beat 中最核心的系统页 / 架构页通常是 hero
- setup beat 的封面页是 hero

## 弧线文件格式

`deck_narrative_arc.md` 应至少包含：

```markdown
# Narrative Arc

## 弧线模板

方案型：setup → tension → tension → resolution → proof → proof → action

## 逐页 Beat

| 页码 | Beat | 情绪目标 | 过渡逻辑 |
|------|------|---------|---------|
| 第 1 页 | setup | 识别感 | 让受众觉得这个问题跟自己有关 → |
| 第 2 页 | tension | 紧迫感 | 放大问题，让受众觉得不能再拖 → |
| ... | ... | ... | ... |

## 信心拐点

第 N 页：从"有问题"到"有方案"的转折。

## 呼吸页

第 N 页：刻意降低密度，给受众消化时间。
```
