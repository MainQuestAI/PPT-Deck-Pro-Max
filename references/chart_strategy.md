# Chart Strategy

## 先选关系，再选图

先问：

1. 这页要表达什么业务关系
2. 什么最简单的图能讲清它

不要先想“做一个很酷的图”。

## 推荐映射

- 对比关系 -> 双栏对比 / 差异表 / 对比条形图
- 阶段关系 -> 阶段带 / 流程图
- 闭环关系 -> 环形闭环 / 中心辐射
- 优先级关系 -> 堆叠层级 / 条形优先级
- 诊断关系 -> 多栏诊断板

## 模板优先

优先复用 `assets/chart_templates/` 里的模板。

模板输入结构请直接看：

- `assets/chart_templates/README.md`

原则：

1. Visual AI 选模板
2. Build AI 映射数据和文案
3. 不鼓励从零写复杂图表代码

## 模板必须包含可执行代码

图表模板不能只是“描述结构的 JSON”。

至少应包含：

1. 实际的 HTML/CSS 或图表配置代码
2. 明确的占位符
3. 最小可运行的结构

Build AI 的职责应是：

**把数据填进模板，而不是从空白页开始发明图表。**

如需把占位符模板渲染成实际代码，可使用：

```bash
python scripts/render_chart_template.py --template <template.html> --data <mapping.json> --output <rendered.html>
```

## 伪图表禁令

以下内容属于伪图表：

1. 只有装饰意义的圆环或发光图形
2. 看起来像分析图，但没有业务变量映射
3. 只是换了形状的项目符号列表
