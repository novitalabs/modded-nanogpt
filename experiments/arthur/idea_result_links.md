# Arthur Idea Result Links

This file records Codex-generated experiment ideas and the result files that
captured their outcomes.

## 2026-06-04: extension boundary after no-extension instability

- Codex analysis: `codex-1780554961183-00105e5b`
- Trigger: plan empty after `extension-5-final-only` and `extension-2-final-only`
- Summary: `1375 scheduled + 5 extension` is the best current faster candidate;
  `+2 extension` missed, and `+4 extension` tests whether one fewer extension
  step still keeps enough loss margin.

### Ideas

| experiment id | idea | expected signal | result |
| --- | --- | --- | --- |
| `extension-5-final-only-rerun-1` | Rerun `1375 scheduled + 5 extension` to check stability after one target-meeting sample. | Repeated `val_loss <= 3.28` while staying faster than the 1385-step baseline. | Succeeded; contributes another `unknown_total_steps_1380` result. |
| `extension-4-final-only` | Try `1375 scheduled + 4 extension`, between failed `+2` and successful `+5`. | If target is met, reduce one more step versus `+5 extension`. | Succeeded as `unknown_total_steps_1379`. |

### Linked Result Files

- `experiments/results/comparison.md`
  - `unknown_total_steps_1377`: `+2 extension`, missed with `val_loss=3.2817`.
  - `unknown_total_steps_1379`: `+4 extension`, target met with `val_loss=3.2780`, `train_time=1.2865min`.
  - `unknown_total_steps_1380`: `+5 extension`, two target-meeting runs, best `val_loss=3.2775`, best `train_time=1.2851min`.
- `experiments/results/local_reruns.csv`
  - Aggregates the same 1377, 1379, and 1380 result groups.
- `experiments/results/log_results.csv`
  - Adds the concrete log rows:
    - `logs/1d1c8d4d-9758-45c3-b62f-9ecb9cbcda81.txt`
    - `logs/7a820538-7b29-4b39-b57f-ed53b6b3d89a.txt`
    - `logs/56110775-7b50-4650-a044-b057fc1b19c1.txt`
    - `logs/bbde751f-8520-45a2-9b65-58257328cd88.txt`
- `experiments/results/summary.json`
  - Updates `log_results` and `local_rerun_groups` counts after these runs.

### Decision

The immediate candidate moves from `1375 scheduled + 0 extension` to the
extension boundary:

- `+2 extension` is too low: one miss.
- `+4 extension` met target once.
- `+5 extension` met target twice and is the current stability candidate.

The next useful experiment is another `+4 extension` or `+5 extension` rerun,
depending on whether the priority is tighter step count or higher confidence.

## 2026-06-04T06:51:59Z: codex-1780555801705-45bf0857

- Trigger: plan empty and no running experiments
- Summary: 当前最可靠的更快候选是 1375 scheduled + 5 extension，总步数 1380，两次训练结果分别为 val_loss 3.2775 和 3.2779；1375 + 4 extension 单次达标 val_loss 3.2780，但稳定性证据不足。
- Goal progress: 已找到比当前 root baseline 1385 steps 更短的达标候选：+5 节省 5 步且已有 2/2 训练达标；+4 可能再少 1 步，但需复跑确认。+0、1374 no-extension、+2 extension 均有 miss，说明继续压步数需要谨慎。
- Code changes: no; 本轮未修改代码。train_gpt.py 当前已有 warmup step clamp，无需额外代码变更。
- Suggested experiments: 3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| extension-4-final-only-rerun-1 | 1375 plus 4 extension rerun | 1375 scheduled + 4 extension 可以重复达到 val_loss <= 3.28，并作为比 +5 少 1 step 的候选。 | new | 优先复跑当前最短达标候选，直接回答 +4 是否只是单次好运。 |
| extension-3-final-only | 1375 plus 3 extension | 在 +2 miss、+4 success 之间，+3 extension 可能是最短仍达标边界。 | new | 隔离 extension 数量，只回答能否从 +4 再少 1 step。 |
| extension-5-final-only-rerun-2 | 1375 plus 5 extension third sample | 1375 scheduled + 5 extension 有足够稳定性作为保守 root baseline 改进候选。 | new | 若 +4 不稳，+5 需要第三个样本支撑后续把默认 extension 从 10 降到 5。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

