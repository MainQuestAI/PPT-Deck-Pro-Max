# Commercial Scorecard

正式评审版不要只回答“做得好不好看”，还要回答“这套 Deck 能不能卖得动”。

建议 Review AI 在完成 `deck_review_findings.json` 之外，再输出 `commercial_scorecard.json`。

## 核心维度

每个维度使用 `1-5` 分：

1. `audience_fit`
   - 这套材料是不是对准了真正的决策者，而不是泛泛而谈。
2. `buying_reason_clarity`
   - 前五页是否已经让客户知道为什么现在值得买或值得启动。
3. `proof_strength`
   - 最强证据是否前置，样例页是否能独立解释产品。
4. `objection_coverage`
   - 关键顾虑是否被正面回答，例如可信度、数据安全、落地门槛。
5. `narrative_flow`
   - 叙事是否顺，是否从问题、方案、证据、合作路径自然推进。
6. `commercial_ask`
   - 最终 CTA 是否清楚，是否能引导到具体商业动作。

## 判定建议

- `overall_score >= 4.0`：可进入正式外发或客户会前精修
- `3.3 <= overall_score < 4.0`：结构基本成立，但仍需针对关键页加强
- `overall_score < 3.3`：不应进入正式外发，必须先返工

## 关键原则

1. 评分卡不是审美意见，而是成交能力判断。
2. 如果得分低，优先回退 `deck_brief.md`、`deck_hero_pages.md`、`deck_clean_pages.md`。
3. 如果一个维度低于 `3`，必须附具体原因和建议动作。
