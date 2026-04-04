# Font Loading Guide

## 目标

确保 Deck 在不同环境下都能使用 theme tokens 指定的字体，而不是 fallback 到系统默认字体。

## 推荐字体

| 用途 | 字体名 | 来源 |
|------|--------|------|
| 标题 | Plus Jakarta Sans | Google Fonts |
| 正文 | Noto Sans SC | Google Fonts |
| 数字/指标 | IBM Plex Sans | Google Fonts |

## HTML Deck 路径

### 方式 1：引用 fonts.css（推荐）

在 HTML deck 的 `<head>` 中加入：

```html
<link rel="stylesheet" href="assets/fonts/fonts.css" />
```

`fonts.css` 文件通过 Google Fonts CDN 加载字体。

### 方式 2：直接引用 Google Fonts

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&family=Noto+Sans+SC:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
```

### Fallback Stack

所有 CSS 中的 font-family 声明应使用完整的 fallback：

```css
font-family: "Plus Jakarta Sans", "Noto Sans SC", system-ui, -apple-system, sans-serif;
```

## PPTX 路径

python-pptx 不支持字体嵌入。PPTX 中指定的字体需要在打开电脑上已安装。

建议：

1. 在团队内共享字体安装包
2. 使用 Google Fonts 下载 TTF/OTF 文件并安装
3. 如果目标受众环境不可控，优先使用系统自带字体（如 Arial、Helvetica、Microsoft YaHei）

## 最佳实践

1. 在 `deck_vibe_brief.md` 中锁字体时，同时说明 fallback 方案
2. Build AI 在生成 HTML 时必须引用 `fonts.css`
3. QA 时检查字体是否正确加载（Chrome DevTools → Computed Styles → font-family）
