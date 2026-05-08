# Solution Deck Minimal

最小样例用于验证编排链路能跑通：`init -> handoff -> qa`。

它不追求最终视觉成品，只验证三件事：

- 项目骨架能初始化
- Build AI 的交接包能生成
- QA 报告能落盘

## 一键 smoke test

```bash
./examples/solution_deck_minimal/run_smoke.sh
```

默认输出到 `/tmp/deck_solution_minimal`。也可以指定输出目录：

```bash
./examples/solution_deck_minimal/run_smoke.sh /tmp/my_deck_smoke
```

## 手动步骤

```bash
python3 scripts/run_deck_pipeline.py init \
  --project-dir /tmp/deck_solution_minimal \
  --pages 3 \
  --preset solution_deck \
  --production-mode quick

python3 scripts/run_deck_pipeline.py handoff \
  --project-dir /tmp/deck_solution_minimal \
  --role build \
  --page-ids slide_01

python3 scripts/run_deck_pipeline.py qa \
  --project-dir /tmp/deck_solution_minimal \
  --write-state
```

完成后重点看：

- `/tmp/deck_solution_minimal/build_handoff.md`
- `/tmp/deck_solution_minimal/deck_review_report.md`
- `/tmp/deck_solution_minimal/slide_state.json`
