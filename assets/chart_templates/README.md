# Chart Templates

这些模板不是“图表示意”，而是可直接填充的 HTML 片段。

原则：

- 优先选模板，再映射数据
- 不要让 Build AI 从零发明图表结构
- 默认对占位符做 HTML 转义
- 如需插入原始 HTML，必须在数据 JSON 中显式声明 `__raw__`

## comparison_bar.html

用途：
- 横向对比
- 指标高低
- 方案对比

输入数据：

```json
{
  "TITLE": "四项关键指标",
  "SUBTITLE": "用于展示当前方案的量化强弱",
  "__raw__": ["ROWS"],
  "ROWS": "<div class=\"row\">...</div>"
}
```

说明：
- `ROWS` 需要传入完整的原始 HTML 行块，因此必须加入 `__raw__`
- 推荐一页不超过 4 到 6 行

## closed_loop.html

用途：
- 闭环机制
- 四阶段系统
- 中心能力 + 四个节点

输入数据：

```json
{
  "CENTER_LABEL": "MirrorWorld",
  "NODE_1_LABEL": "输入",
  "NODE_1_TEXT": "接收真实业务问题与素材",
  "NODE_2_LABEL": "运行",
  "NODE_2_TEXT": "调度消费者镜像与研究动作",
  "NODE_3_LABEL": "输出",
  "NODE_3_TEXT": "生成反馈、判断与建议",
  "NODE_4_LABEL": "回写",
  "NODE_4_TEXT": "沉淀为后续可复用资产"
}
```

说明：
- 所有字段默认会被安全转义
- 适合用于系统页、闭环页、研究流程页

## stage_band.html

用途：
- 阶段关系
- 流程页
- 方法分步说明

输入数据：

```json
{
  "TITLE": "四个研究阶段",
  "SUBTITLE": "从任务定义到结果回写",
  "__raw__": ["BANDS"],
  "BANDS": "<div class=\"band\">...</div>"
}
```

说明：
- `BANDS` 需要传入完整原始 HTML 行块，因此必须加入 `__raw__`
- 推荐 3 到 5 个阶段

## priority_stack.html

用途：
- 优先级关系
- 路线排序
- 试点优先级

输入数据：

```json
{
  "TITLE": "首批试点优先级",
  "SUBTITLE": "先做最容易形成 ROI 的场景",
  "__raw__": ["STACKS"],
  "STACKS": "<div class=\"stack\">...</div>"
}
```

说明：
- `STACKS` 需要传入完整原始 HTML 行块，因此必须加入 `__raw__`
- 推荐 3 到 4 层

## diagnostic_board.html

用途：
- 多栏诊断板
- 摘要页
- 诊断关系

输入数据：

```json
{
  "TITLE": "为什么现在做、做什么、做到什么算成立",
  "SUBTITLE": "用三栏快速建立商业判断",
  "__raw__": ["COLUMNS"],
  "COLUMNS": "<div class=\"column\">...</div>"
}
```

说明：
- `COLUMNS` 需要传入完整原始 HTML 行块，因此必须加入 `__raw__`
- 推荐固定 3 栏

## 数据映射约束

- 数值、标签、客户名、场景名必须保真，不要为了排版擅自改写
- 如果内容过长，优先拆页或换模板，而不是把文本硬塞进图表
- 如果模板不适配业务关系，应先回到 `references/chart_strategy.md` 重新选图，而不是强行拼装
