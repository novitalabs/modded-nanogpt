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


## 2026-06-04T06:59:50Z: codex-1780556282012-cfa70b64

- Trigger: plan empty and no running experiments
- Summary: 当前最佳候选是 1375 scheduled + 4 extension，总步数 1379，两次结果为 val_loss 3.2780 和 3.2787，均达标且快于 root baseline 1385 steps。+3 extension 单次 3.2801 未达标，+2 extension 和 no-extension 边界也不稳定。
- Goal progress: 已经从 root baseline 约 1.2948min 的达标训练时间推进到 +4 extension 约 1.2864min，节省 6 个总 step 且目前 2/2 达标。缺口是 +4 仍只有两个样本，稳定性证据还不够强；+3 是否可用仍需复跑确认。
- Code changes: no; 本轮未修改代码；train_gpt.py 中 warmup step clamp 已存在。
- Suggested experiments: 3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| extension-4-final-only-rerun-2 | 1375 plus 4 extension third sample | 1375 scheduled + 4 extension 可以第三次稳定达到 val_loss <= 3.28，成为优先替代 root baseline 的更快候选。 | new | 优先验证当前最快 2/2 达标候选的稳定性。 |
| extension-3-final-only-rerun-1 | 1375 plus 3 extension rerun | 1375 scheduled + 3 extension 上次只以 3.2801 轻微 miss；复跑可判断它是可挽回的边界噪声还是应淘汰的低余量设置。 | new | 隔离 extension 数量，只回答能否从 +4 再少 1 step。 |
| extension-5-final-only-rerun-2 | 1375 plus 5 extension fallback sample | 如果 +4 后续出现 miss，1375 scheduled + 5 extension 仍可能是更稳的 baseline 改进候选。 | new | +5 已有两个达标日志；第三样本用于和 +4 稳定性对照。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T07:09:08Z: codex-1780556761615-62f65059

- Trigger: plan empty and no running experiments
- Summary: 当前最佳可采用候选是 1375 scheduled + 4 extension，总步数 1379，已有 3/3 训练日志达标；Arthur 把第三次标为 failed 是 check 字段执行失败导致，run exit_code 和日志均为成功。
- Goal progress: 已把 root 默认总步数从 1385 降到 1379，预计达标训练时间从约 1.2948min 降到约 1.2864min，节省 6 个 step；缺口是还需要用修改后的 root train_gpt.py 直接复跑确认。
- Code changes: yes; 修改 train_gpt.py：将 Hyperparameters.num_extension_iterations 默认值从 10 降为 4，对齐已验证的 1379-step 候选。
- Suggested experiments: 2

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| current-root-extension4-rerun-1 | Validate new root extension-4 default | 修改后的 root train_gpt.py 默认 1375 scheduled + 4 extension 可以直接达到 val_loss <= 3.28，并复现约 1.286min 训练时间。 | new | 这是代码变更后的必要确认；命令自身会在 final val_loss > 3.28 时非零退出。 |
| extension-5-from-ext4-root-fallback | Extension 5 fallback from new root | 如果 +4 默认复跑边际不足，+5 extension 能提供更大 loss margin，同时仍比旧 1385-step baseline 少 5 step。 | new | 只改变 extension 数量，作为 +4 新默认不稳时的保守回退证据。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T07:18:10Z: codex-1780557361222-4f76b6c7

- Trigger: plan empty and no running experiments
- Summary: 当前可采用的保守更快候选是 1375 scheduled + 5 extension，总步数 1380；已有 3/3 日志达标，val_loss 分别约 3.2775、3.2779、3.2778。+4 虽有 3 个达标样本，但最新 root 直接复跑 val_loss=3.2804 miss，稳定性不足。
- Goal progress: 相比旧 root baseline 1385 steps、约 1.2948min 的达标训练时间，+5 默认总步数 1380，目标内训练时间约 1.2864min，节省 5 步且当前达标率证据更稳。缺口是还需要用修改后的 root train_gpt.py 直接跑至少 1 次确认默认路径。
- Code changes: yes; 修改 train_gpt.py：将 Hyperparameters.num_extension_iterations 默认值设为 5，替代上轮不稳定的 +4 默认。
- Suggested experiments: 2

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| current-root-extension5-rerun-1 | Validate new root extension-5 default | 修改后的 root train_gpt.py 默认 1375 scheduled + 5 extension 可以直接达到 val_loss <= 3.28，并保持约 1.286-1.289min 训练时间。 | new | 代码默认值已改为 +5；这是提交前最关键的 root 路径验证。 |
| current-root-extension5-rerun-2 | Extension-5 default stability sample | 1375 scheduled + 5 extension 在 root 默认路径上可以连续复现达标，支撑把默认 extension 从旧 10 降到 5。 | new | 若第一条过线，第二条补稳定性样本；若第一条失败，则说明 +5 默认仍需重新评估。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

