# Build Contract

## 目标

定义构建层（Codex/subagent + HTML 装配）与编排层之间的接口合同。

本版本默认采用 image-led build：

1. 先执行 `image_build_jobs.json` 中的当前批次生图任务
2. 生图结果批准后，再进入 HTML 装配
3. proof 页没有 approved/embedded 资产时，不视为构建完成

## HTML Deck 组装规范

### 页面结构

每一页用一个 `<section>` 元素包裹：

```html
<section class="slide" data-slide="slide_01" data-beat="setup">
  <!-- 页面内容 -->
</section>
```

### 必要属性

- `data-slide` — 对应 `slide_state.json` 的 `page_id`
- `data-beat` — 对应 `deck_narrative_arc.md` 的 beat 类型

### 字体加载

在 `<head>` 中引用 `assets/fonts/fonts.css`。

### Speaker Notes

如果 `speaker_notes.json` 或 `build_context.json` 中包含 speaker notes，写入：

```html
<aside class="notes" aria-hidden="true">演讲备注内容</aside>
```

### 配图资产

如果 `build_context.json` 的 `inputs.assets` 包含当前页的已批准图片引用：

```html
<img src="assets/dashboard_main.png" alt="产品仪表盘" class="product-screenshot" />
```

使用 `position` 字段控制布局位置。

如果 `build_context.json` 的 `inputs.generation_jobs` 包含当前页待生成任务：

- 先按 job 的 `prompt_payload` 生成图片
- 同一批次默认最多 3 页，先确认关键页效果，再继续后续批次
- 生成完成后，将对应资产状态更新为 `generated` / `approved`，并回写 `asset_manifest.json`
- HTML 装配层只消费 `approved` 或 `embedded` 资产；`queued/generated/rejected` 不应当被假装当成完成资产

### 翻页

由构建 Skill 决定翻页实现（键盘、滑动、按钮），不在编排层规定。

## PPTX 组装规范

### Slide 顺序

严格按 `slide_state.json` 的 `pages` 数组顺序生成 slide。

### Speaker Notes

用 `python-pptx` 写入：

```python
slide.notes_slide.notes_text_frame.text = "演讲备注内容"
```

或使用 `scripts/inject_speaker_notes.py` 后处理注入。

### 配图资产

用 `python-pptx` 插入图片：

```python
slide.shapes.add_picture("assets/dashboard_main.png", left, top, width, height)
```

位置和尺寸参考 `deck_page_skeletons.md` 中的视觉区域边界。

PPTX 在本轮不是 image-led 首要路径，不要求消费 `image_build_jobs.json`；优先保障 HTML 路径先跑通。

## 输出文件命名

不要硬编码 `v1.pptx` 或 `v1.html`。

推荐命名：`{project_id}_deck.pptx`、`{project_id}_deck.html`、`index.html`。

`validate_deck_outputs.py` 使用动态 glob 发现，支持任意命名。
