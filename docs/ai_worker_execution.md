# AI Worker Execution Guide

给 Claude Code / OpenCode / Codex worker 的执行说明。

## 任务定位

你负责执行 Deck Production Orchestrator 的某个阶段。不要扩展任务范围；只处理交接包指定的页、角色和产物。

## 输入优先级

1. `build_handoff.md` / `*_handoff.md`
2. `contexts/*.json`
3. `deck_clean_pages.md`
4. `deck_visual_composition.md`
5. `deck_visual_system.md`
6. `deck_component_tokens.md`
7. `deck_theme_tokens.json`
8. `deck_expert_context.md`
9. `slide_state.json`

如果输入之间冲突，先以 handoff 和 context 为准，并在输出里记录冲突点。

## 执行边界

- Build worker：只构建指定页，最多处理一个 batch。
- Visual worker：只改视觉系统、tokens、composition 相关文件。
- Review worker：只输出 findings、scorecard、rollback plan，不直接修页面。
- Rework worker：只处理 rollback plan 指定的问题。

## 质量标准

- 每页必须有视觉主角：图表、流程、指标、架构、截图或概念 UI。
- 客户可见文案不能泄露内部编排术语，例如 hero page、proof beat、CTA design。
- proof 页优先使用真实截图；没有截图时使用概念 UI 骨架，避免空占位。
- 输出 HTML 时保持 16:9 页面比例和稳定几何；输出 PPTX 时保持元素可编辑。
- 改完必须生成或更新 QA 所需产物。

## 推荐命令

先检查环境：

```bash
python3 scripts/run_deck_pipeline.py doctor
```

生成 build handoff：

```bash
python3 scripts/run_deck_pipeline.py handoff \
  --project-dir ./my-deck \
  --role build \
  --page-ids slide_01
```

生成 batch dispatch：

```bash
python3 scripts/run_deck_pipeline.py dispatch-build \
  --project-dir ./my-deck \
  --batch-id batch_01
```

收口 QA：

```bash
python3 scripts/run_deck_pipeline.py qa \
  --project-dir ./my-deck \
  --write-state
```

正式验收：

```bash
python3 scripts/run_deck_pipeline.py validate \
  --project-dir ./my-deck \
  --output-mode pptx+html \
  --formal
```

## 交付回报格式

执行完成后只汇报：

- 改了哪些文件
- 生成了哪些产物
- 哪些检查已通过
- 哪些问题仍需上游角色或人工确认

不要把完整中间文件贴回对话。文件已经在项目目录里。
