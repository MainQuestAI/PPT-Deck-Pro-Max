# Context Handoff Rules

## 总原则

不要把所有上下文丢给所有 AI 角色。

## Brief / Narrative AI

可见：

- 原始需求
- 长文档
- 历史主张
- `review_rollback_plan.md` 中分配给 `brief` 的返工项（如果存在）

不可见：

- 大段实现代码
- 视觉补丁细节

## Visual System AI

可见：

- `deck_brief.md`
- `deck_vibe_brief.md`
- `deck_hero_pages.md`
- `deck_clean_pages.md`
- `review_rollback_plan.md` 中分配给 `visual` 的返工项（如果存在）

不可见：

- 原始长文档
- 内部评审对话

## Deck Build AI

可见：

- 当前页或最多 3 页的 `deck_clean_pages.md` 节点
- `deck_visual_system.md`
- `deck_component_tokens.md`
- `deck_theme_tokens.json`
- `slide_state.json`
- `review_rollback_plan.md` 中与当前页相关的返工项（如果存在）

不可见：

- 原始长文档
- 历史评审对话
- 其他页面的大段实现代码

## Review AI

可见：

- `review_package.json`
- 成品 deck
- 缩略总览
- `deck_clean_pages.md`
- `slide_state.json`
- `review_findings.schema.json`

不可见：

- 预设答案
- 主观诊断结论

优先级规则：

1. 先看 `review_package.json`
2. 再按 package 中的 `montage` 和页级 PNG 做多模态判断
3. 最后回看文字与状态文件

## 构建期硬规则

Build AI 默认按单页生成，最多 3 页小批次。  
每次生成前必须重置上下文。

建议通过 `scripts/context_manager.py` 生成上下文包，而不是手动拼接。

## 返工期硬规则

不要把完整的 `review_rollback_plan.md` 原样转发给所有 AI 员工。  
优先使用按角色过滤的返工 handoff，只让：

1. `brief` 看到业务主线返工项
2. `visual` 看到视觉系统与几何返工项
3. `build` 看到需要重建的页面和对应 build context
