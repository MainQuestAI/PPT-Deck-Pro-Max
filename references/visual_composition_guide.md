# Visual Composition Guide

## 目标

指导 AI 从 `deck_clean_pages.md` 的文字内容，自主生成 `deck_visual_composition.md` — 一份逐页视觉施工图，让 Build AI 拿到的不再是"文字描述"而是"视觉规格"。

## 核心原则

**每一页的视觉组合必须回答三个问题：**

1. **视觉主角是什么？**（图表/图标链/大数字/架构图/截图）
2. **文字如何配合视觉主角？**（左文右图？上文下图？环绕？）
3. **观众的眼睛应该先看什么？**（视觉重量分布）

**如果回答不出这三个问题，说明这页还停留在"文字排版"阶段。**

## 生成 Visual Composition 的步骤

### Step 1：识别每页的核心数据关系

读取 `deck_clean_pages.md` 的每一页，判断内容本质上是什么数据关系：

- 如果有"A vs B"、"传统 vs 下一代"、"旧做法 vs 新做法"→ **对比关系**
- 如果有"断裂"、"不足"、"差距"、"覆盖率低"→ **程度/缺口**
- 如果有"先…再…然后…最后"、"流程"、"阶段"→ **阶段/流程**
- 如果有"闭环"、"循环"、"持续运转"、"反馈回流"→ **闭环**
- 如果有"五类"、"六大模块"、"三个场景"→ **分类/并列**
- 如果有"6.02 亿"、"100+"等单一冲击力数字→ **大数字**

### Step 2：为每页选择视觉主角

参考 `references/information_design_guide.md` 的映射规则，为每页选择最合适的视觉形式。

**关键：不是每页都需要复杂图表。但每页都需要一个"视觉主角"——可以是图表，也可以是 icon 流程链、大数字、或架构图。**

### Step 3：决定布局组合

常用布局组合：

| 名称 | 结构 | 适用场景 |
|------|------|---------|
| 左文右图 | 文字 40% / 视觉 60% | 有一个核心图表或截图 |
| 上叙下图 | 标题区 20% / 图表区 60% / 底部 20% | 闭环图、架构图 |
| 三栏卡片 | 等宽三栏，每栏有 icon + 数据 | 三个并列概念 |
| 上流程下表格 | 流程链 30% / 对比表 + 图表 70% | 场景页 |
| 全幅表格 | 表格占主体 | 多维度对比 |
| 中心大数字 | 大数字居中，配注释 | 冲击力数据 |

### Step 4：指定视觉细节

每页必须指定：

1. **icon 指定**——不要写"适当 icon"，必须写具体是什么（brain / gear / chart / target / shield / rocket / ...）
2. **颜色指定**——每个视觉元素的具体颜色，引用 theme token
3. **说明性数据**——如果原稿没有数字但概念可量化，推断合理数值并标记 `illustrative=true`
4. **图表模板引用**——如果 `assets/chart_templates/` 有匹配的模板，引用它

### Step 5：标注说明性数据

参考 `references/illustrative_data_guide.md`。所有 AI 推断的数据必须标记：

```
指标：深层意图理解率 | value=25% | illustrative=true
```

## `deck_visual_composition.md` 的完整格式

```markdown
# Visual Composition

## 第 N 页

页面标题：传统 CDP/MA 的三层断裂

### 数据关系
类型：degree_gap（程度/缺口）
识别依据：三个概念各有"已有"和"缺失"的描述，本质是量化三个维度的缺口

### 视觉主角
类型：gauge_chart
数量：3
位置：每栏底部
占页面比例：30%

### 布局组合
结构：三栏等宽卡片
每栏结构：icon → 标题 → 已有(绿) / 缺失(红) → gauge_chart
视觉重量：gauge_chart 是主角，标题是辅助，描述是补充

### 数据可视化
指标 1：label=深层意图理解率 | value=25% | type=gauge | color=#ff8b5c | illustrative=true
指标 2：label=策略动态调整率 | value=20% | type=gauge | color=#a78bfa | illustrative=true
指标 3：label=个性化内容命中率 | value=30% | type=gauge | color=#16c79a | illustrative=true

### Icon 指定
栏 1：icon=brain | label=认知层断裂 | color=#ff8b5c
栏 2：icon=settings | label=决策层断裂 | color=#a78bfa
栏 3：icon=file-text | label=内容层断裂 | color=#16c79a

### 强调方式
已有能力：✅ 绿色标记
缺失能力：❌ 橙红色标记

### 图表模板引用
模板：diagnostic_board.html
```

## 常见错误

1. **写了"视觉主角: 三栏卡片"但没写每栏里面有什么**→ 不够，必须写到 icon + 数据 + 颜色
2. **所有页面都选了相同的视觉类型**→ 检查是否有更合适的形式，13 页应该至少有 5 种不同的视觉主角类型
3. **说明性数据的值不合理**→ 25% 的"理解率"比 95% 更能表达"断裂"的冲击力
4. **icon 只写了 emoji**→ 应指定 Lucide/Heroicons 风格的 icon name，Build AI 用 SVG 渲染
