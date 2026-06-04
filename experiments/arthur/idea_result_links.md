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


## 2026-06-04T11:29:02Z: codex-1780572542015-d83be8a8

- Trigger: 1 run(s) finished
- Summary: block3_skip_off 完成 1380/1380，val_loss=3.2798、train_time_min=1.2776、target_met=true。该结果没有给出强退化信号；结合 embedding_skip_off=3.2779，skip family 在当前 root 中应暂时降为边界候选，而不是强 top10 证据。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖 skip family 的 embedding 和 block3 两个拆分项。本轮补齐 block3 skip 首样本；剩余缺口主要是 residual decay 首样本，以及 QK/EoS/cautious WD 等稳定性样本。block3 skip 因结果贴近 3.280 阈值，需要一个复跑来确认是否只是噪声。
- Code changes: no; 未修改源码；本轮只分析 readme-top10-block3-skip-off 运行结果，并追加实验日志。运行产物已由实验脚本落盘，等待 Arthur 提交。
- Suggested experiments: 1
- Pending result runs: readme-top10-block3-skip-off-1780572181-fd70e2f0
- Linked experiment ids: readme-top10-block3-skip-off
- Input code commits: b7bdb28ce42e2fd54362a05644539217feb924ce

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-block3-skip-off-rerun1 | Block3 skip stability sample | 第二个 block3_skip_off 样本将判断 3.2798 的边界结果是否稳定；若仍 target_met 且接近 baseline，则 block3 skip 当前因果贡献应降级。 | new | block3 skip 是历史 skip-family 高先验项，但首样本只在阈值边缘，不能单样本定级。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/readme_top10_ablation_results.csv`
- `experiments/results/readme_top10_readme_top10_block3_skip_off.json`
- `experiments/results/summary.json`

## 2026-06-04T10:19:09Z: codex-1780567982051-0da1b9b7

- Trigger: 1 run(s) finished
- Summary: `readme_top10_batch_schedule_constant_mean_local` 完成 1380/1380 且 run exit code 为 0；Arthur 状态为 failed 是因为 `target_met=false`，不是训练或脚本失败。该等均值 batch ablation 得到 `val_loss=3.3004`、`train_time_min=1.2898`、`step_avg=56.08ms`，相比当前 root/target 附近样本属于明显 loss 退化而无速度收益，说明 8/16/24 batch ramp 在当前 root 上有独立正贡献；之前 `constant_final` 的低 loss 主要混入了额外 token/更慢训练预算，不能作为同一问题的干净证据。
- Goal progress: README record-history delta 先验已建立，当前 ablation 已覆盖大部分历史 top10 候选。当前强证据层级为 Polar Express/Muon 子项最强，EoS alignment 单样本 nan，value embeddings 与 bigram hash embedding 双样本稳定退化，long-window 多样本稳定退化，batch schedule 有一个干净等均值负向样本，QK norm 单样本中等退化。主要缺口仍是 EoS/QK/batch schedule 的稳定性样本，以及 block3 skip、cautious WD、residual decay 的首样本证据；现有队列已覆盖大部分缺口，本轮只建议补一个等均值 batch 复跑。
- Code changes: no; 未修改训练代码或运行脚本。仅追加本分析记录；结果 CSV/JSON/汇总文件来自刚完成的 run/collect_results。
- Suggested experiments: 1
- Pending result runs: readme-top10-batch-schedule-constant-mean-local-1780567741-d44e4079
- Linked experiment ids: readme-top10-batch-schedule-constant-mean-local
- Input code commits: 09d7ea1e2ae6cfa4a68703447f34166f7d97191b

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-batch-schedule-constant-mean-rerun1 | Mean batch schedule stability | 如果 16/16/16 等均值常量 batch 再次给出约 3.30 loss 且速度无收益，则 batch size ramp 可从预算混淆中剥离出来，作为当前 top10 的稳定因果证据。 | new | 首个 constant_mean 样本有效但只有一次；该变量历史先验靠后但当前等预算信号接近 bigram/long-window，值得复跑一次确认方差。 |

### Linked Result Files

- `experiments/results/readme_top10_ablation_results.csv`
- `experiments/results/readme_top10_readme_top10_batch_schedule_constant_mean_local.json`
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


## 2026-06-04T07:39:59Z: codex-1780558561595-1171be05

- Trigger: 1 run(s) finished
- Summary: 历史先验已给出 README top10；当前因果证据新增 XSA-off 单样本，结果变差且未达标，但需要重复样本或与相邻 baseline 交错确认噪声。Bigram 正在运行，其余若干小特性已排队。
- Goal progress: 已完成历史排序，并开始当前代码可逆 ablation。缺口是 top10 中 FP8 lm_head/softcap、batch size schedule、EoS-aligned batches 还没有当前反事实结果；Muon 和现代架构整体仍需要更谨慎拆分实验。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh，新增 fp8_lm_head_off、batch_schedule_constant_final、eos_alignment_off 三个临时 ablation 分支；未修改 train_gpt.py。
- Suggested experiments: 3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-fp8-lm-head-off | Ablate FP8 lm_head | 关闭 FP8 lm_head 会量化 README top10 中 FP8 head/softcap/logit rescale 家族在当前代码中的速度与 loss 贡献。 | new | 历史先验 rank 5，尚无当前 ablation；脚本已支持该可逆分支。 |
| readme-top10-batch-schedule-constant-final | Ablate batch schedule | 把前两阶段 batch size 改为最终 batch size，可隔离 batch size ramp 是否仍改善收敛/速度。 | new | 历史先验 rank 8；该实验只改变 batch schedule，保留其它 schedule。 |
| readme-top10-eos-alignment-off | Ablate EoS batch alignment | 训练 batch 不再从 BOS/EoS 边界对齐会量化 EoS-aligned batches 在当前代码中的贡献。 | new | 历史先验 rank 10；验证数据仍保持原设置，仅关闭训练 batch 对齐。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T08:03:05Z: codex-1780559941818-a0b08a3d

- Trigger: 1 run(s) finished
- Summary: 以现有 1380-step 达标样本 val_loss≈3.2778 为粗参照，已观测 ablation 退化排序为 value_embeds_off +0.0346、bigram_off +0.0245、mtp_off +0.0095、xsa_off +0.0057、smear_off +0.0049。当前结论仍是 provisional。
- Goal progress: README 历史先验已建立；当前代码已有 5 个单因素 ablation 指标，但 bigram/value 需要干净重跑，FP8/EoS/PKO 还缺有效当前证据，batch schedule 正在等待结果。
- Code changes: no; 本轮未修改代码；仅检查了 ablation 脚本语法和结果文件。
- Suggested experiments: 5

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-fp8-lm-head-off-local | Ablate FP8 lm_head on .72 | 只关闭 lm_head 的 FP8 matmul 路径会量化 FP8 head 在当前代码中的速度和 loss 贡献。 | new | 上一条 FP8 失败原因是 .75 pod NotFound；改用已可用的 .72 pod 获取有效证据。 |
| readme-top10-value-embeds-off-clean-rerun | Clean value embeddings ablation | 关闭 value embeddings 会稳定造成最大 loss 退化，确认其当前 top10 因果贡献。 | new | 已有训练结果很强，但 Arthur run 被旧脚本 EOF 标失败；需要 clean rerun。 |
| readme-top10-bigram-off-clean-rerun | Clean bigram embedding ablation | 关闭 bigram hash embedding 会稳定造成显著 loss 退化，确认其当前因果贡献。 | new | 已有单样本退化仅次于 value embeddings，但 run 状态同样不干净。 |
| readme-top10-eos-alignment-off-local | Ablate EoS alignment on .72 | 关闭训练 batch 的 BOS/EoS 对齐会量化 README rank10 数据对齐方法的当前贡献。 | new | 现有 queued 命令可能仍指向 .75；用 .72 避免环境失败。 |
| readme-top10-pko-off-local | Ablate Partial Key Offset on .72 | 关闭 Partial Key Offset 可判断这个较新的 attention 细节是否超过 smear/XSA/MTP 等小项。 | new | 补齐当前代码中尚未测量的 attention 小特性，且单变量隔离。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T08:21:34Z: codex-1780561081184-de750bad

- Trigger: plan empty and no running experiments
- Summary: 当前 provisional 因果排序：value_embeds_off 平均 +0.0360 loss，bigram_off 平均 +0.0229，mtp_off +0.0095，xsa_off +0.0057，smear_off +0.0049，fp8_lm_head_off +0.0027，partial_key_offset_off +0.0018。bigram clean rerun 虽被 Arthur 标 failed，但日志和 JSON 已有完整 final_result，失败来自脚本尾部 shell 错误，不应丢弃训练结果。
- Goal progress: 历史先验 top10 已建立，当前代码已有 7 个单因素 ablation 证据；缺口是 README 历史 top10 中 EoS alignment、batch schedule、zero projection init、embedding/block skips、QK norm/modern architecture 仍缺当前反事实结果，Muon 和 FA3/window family 还需要更谨慎拆分。
- Code changes: no; 本轮未修改代码；仅检查了 ablation 脚本、结果表和失败日志。
- Suggested experiments: 5

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-eos-alignment-off-local | Ablate EoS alignment on .72 | 关闭训练 batch BOS/EoS 对齐会量化 README top10 中 EoS-aligned batches 的当前贡献。 | new | 上一条失败仅因 .75 pod NotFound；改用已可用的 .72 pod 补有效因果证据。 |
| readme-top10-batch-schedule-constant-final-local | Ablate batch schedule on .72 | 把前两阶段 batch size 改成最终 batch size，可隔离 batch size ramp 对当前收敛和速度的贡献。 | new | 上一条同样因 .75 pod NotFound 无效；这是历史 top10 里尚未测到的调度变量。 |
| readme-top10-zero-mlp-proj-init-off | Ablate zero projection init | 取消 MLP projection zero init 会量化历史 rank3 zero-init 在当前 root 中的因果贡献。 | new | 历史先验很高，脚本已有可逆分支，单变量明确。 |
| readme-top10-embedding-skip-off | Ablate embedding skips | 关闭 embedding-to-block skip 注入会量化 README skip connection family 的主要当前贡献。 | new | 历史 rank4 仍未有当前 ablation；先测 embedding skip，避免和 block3 skip 混在一起。 |
| readme-top10-qk-norm-off | Ablate QK norm | 关闭 QK norm 可为 modern architecture family 提供一个可逆、局部的当前因果样本。 | new | modern architecture 整体不可一次性公平 ablate；QK norm 是可隔离的高先验子项。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T08:31:53Z: codex-1780561501969-4caa7641

- Trigger: 1 run(s) finished
- Summary: 当前因果证据暂列：value embeddings 和 bigram hash embedding 最强；EoS alignment 关闭导致 val_loss=nan，需用修复后的解析器正式记录；MTP/XSA/smear/FP8 是小到中等信号；PKO 当前近似中性；batch schedule 旧结果无效，需修复后重跑。
- Goal progress: README 历史先验 top10 已建立，当前代码已有 value、bigram、MTP、XSA、smear、PKO、FP8、EoS 的单因素证据或日志；缺口是 batch schedule 的有效结果、zero init 排队结果、skip family 和 modern architecture 子项如 QK norm 的当前反事实证据。Muon 和 FA3/window family 仍需要更谨慎拆分。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：结果解析支持 nan/inf val_loss 并将非有限 loss 标为 target_met=false；batch_schedule_constant_final 变体把 TRAIN_MAX_NUM_DOCS[49152] 扩到 256，避免 constant-final batch 在早期 seq_len 下因 cum_seqlens 容量崩溃。
- Suggested experiments: 4

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-batch-schedule-constant-final-local-fixed | Fixed batch schedule ablation | 把前两阶段 batch size 改为最终 batch size 后，若 dataloader 容量足够，可隔离 batch size ramp 对当前收敛和速度的贡献。 | new | 上一条 batch schedule 在 step 50 因 cum_lengths 容量失败；脚本已修复该采集问题，需要重跑获取有效证据。 |
| readme-top10-eos-alignment-off-local-nan-record | Record EoS alignment ablation | 关闭训练 batch BOS/EoS 对齐会破坏最终验证稳定性，修复后的解析器应把 nan loss 作为有效反事实证据记录下来。 | new | 已有日志显示 val_loss:nan，但旧解析器把它误判为无验证结果；需要干净结果文件。 |
| readme-top10-embedding-skip-off | Ablate embedding skips | 关闭 embedding-to-block skip 注入会量化 README rank4 skip connection family 的主要当前贡献。 | new | skip family 历史先验高，当前还没有隔离 ablation。 |
| readme-top10-qk-norm-off | Ablate QK norm | 关闭 QK norm 可为 README rank1 modern architecture family 提供一个局部、可逆的当前因果样本。 | new | modern architecture 整体不可公平一次性关闭；QK norm 是当前代码中清晰可隔离的子项。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T08:52:51Z: codex-1780562881307-8868132d

- Trigger: plan empty and no running experiments
- Summary: 当前最强当前代码 ablation 信号：value_embeds_off 平均 val_loss 3.3138，bigram_off 平均 3.3007，eos_alignment_off 得到 nan；MTP/XSA/smear/FP8 也会轻中度恶化。batch_schedule_constant_final 训练完成且 val_loss 3.2346，但耗时 1.8595min，说明 batch schedule 主要是速度优化而非单纯降 loss。
- Goal progress: README 历史先验 top10 已建立，当前已有 13 条可解析 ablation 记录。缺口是历史 rank1 modern architecture 只缺局部拆分证据，rank2 Muon 还没有安全完整反事实，rank7 long-window/YaRN 尚未测，skip family 只测了 embedding skip 还缺 block3 skip。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：新增 long_window_yarn_off、cautious_wd_off、residual_decay_off 可逆 ablation 分支；未修改 train_gpt.py。已通过 bash -n 和新增/待跑 ablation 替换串 dry-run。
- Suggested experiments: 5

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-qk-norm-off | Ablate QK norm | 关闭 QK norm 可为 README rank1 modern architecture family 提供局部当前因果证据。 | new | 最高历史先验仍缺当前反事实；QK norm 是可安全隔离的子项。 |
| readme-top10-long-window-off | Ablate long windows | 把长窗口层改为短窗口可隔离 long-short sliding window pattern 的当前贡献。 | new | 覆盖历史 rank7 FA3/window family 中最清晰可逆的单变量。 |
| readme-top10-block3-skip-off | Ablate block3 skip | 关闭 block3-to-layer6 skip 可补足 skip connection family 中非 embedding skip 的当前贡献。 | new | embedding_skip_off 单样本近中性，需拆开 block skip 判断 skip family 排名。 |
| readme-top10-polar-express-off | Ablate Polar Express | 用普通 momentum 更新替代 Polar Express 可给 Muon optimizer family 提供一个当前反事实样本。 | new | 完整 Muon-off 代价太大；先测优化器 family 中已有可逆分支。 |
| readme-top10-cautious-wd-off | Ablate cautious WD | 把 cautious weight decay 改回普通 decoupled WD 可量化该 optimizer regularization 技巧的当前贡献。 | new | 历史先验虽低于 top10，但与 optimizer family 排名相关，且单变量明确。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:03:03Z: codex-1780563541630-e4f69ab5

- Trigger: batch finished with results pending commit
- Summary: qk_norm_off 成功落盘：val_loss=3.2907, step_avg=57.20ms, target_met=false。当前有限 loss 信号中 value embeddings 和 bigram 最强，qk_norm 次于它们但强于 xsa/smear/fp8/pko；EoS alignment off 为 nan，batch_schedule_constant_final 低 loss 但明显更慢。
- Goal progress: README historical top10 先验已建立，当前代码已有 value、bigram、EoS、FP8、zero init、embedding skip、QK norm、MTP、smear、PKO、batch schedule 的反事实证据；long-window 与 block3-skip 已 queued。主要缺口是 Muon optimizer family 的当前因果证据，以及 qk_norm、batch schedule 这类关键信号的稳定性样本。
- Code changes: no; 本轮未修改代码；只核对了 qk_norm_off 结果、现有 ablation 脚本和结果汇总。
- Suggested experiments: 4
- Pending result runs: readme-top10-qk-norm-off-1780563181-df979e2f
- Linked experiment ids: readme-top10-qk-norm-off
- Input code commits: 274f6e0a4b149a76d5e419bd5b8dc673e808158b

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-polar-express-off | Ablate Polar Express | 把 Polar Express 替换为普通 Nesterov/momentum 更新，可隔离 Muon optimizer family 中正交化更新的当前贡献。 | new | Muon 是 historical rank2，但完整 Muon-off 牵动参数分组和通信；Polar Express 是当前脚本里最干净的 optimizer 子项。 |
| readme-top10-cautious-wd-off | Ablate cautious WD | 关闭 cautious weight decay 后，若 val_loss 或速度变化明显，可量化 optimizer regularization 对当前 root 的贡献。 | new | 补 optimizer family 的第二个独立子证据，变量单一且脚本已有可逆分支。 |
| readme-top10-qk-norm-off-rerun1 | QK norm stability sample | qk_norm_off 的 +loss 信号若可复现，则 modernized architecture family 在当前 root 的排名应上调。 | new | QK norm 是 historical rank1 family 的局部证据；当前只有一个样本，值得复核方差。 |
| readme-top10-residual-decay-off | Ablate residual decay | 关闭 residual stream exponential decay 初始化后，可判断该 README 技巧是否在当前 root 中仍有独立贡献。 | new | rank 较低但脚本已有分支，可补足 top10 之外可能混入 optimizer/architecture 排名的局部技巧。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:10:21Z: codex-1780564021210-908b92f6

- Trigger: 1 run(s) finished
- Summary: 当前因果证据显示 polar_express_off 最强但需复跑确认；eos_alignment_off 为 nan；value_embeds_off 与 bigram_off 有稳定正向贡献；qk_norm_off、mtp_off、xsa_off、smear_off 为较弱正贡献；batch_schedule_constant_final 降低 loss 但明显变慢，主要应按速度/预算效果评估。
- Goal progress: README historical top10 先验已建立，当前代码已有多数关键 ablation 证据。缺口是 long_window_off 尚无训练结果，block3_skip/cautious_wd/qk_norm stability 仍在队列中，polar/eos 这类极强或异常信号还需要稳定性样本后才能给最终 top10 排名。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：增加无 kubectl 或 RUN_README_ABLATION_DIRECT=1 时的 direct runner，保留有 kubectl 时原 pod 执行路径；未修改 train_gpt.py。
- Suggested experiments: 4
- Pending result runs: readme-top10-polar-express-off-1780563841-f899d1ef, readme-top10-long-window-off-1780563841-acb0619f
- Linked experiment ids: readme-top10-long-window-off, readme-top10-polar-express-off
- Input code commits: d4ef31d93ac234b0d74390b503ffa3b0422189ab

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-long-window-off-local-fallback | Retry long windows ablation | 把长窗口层改为短窗口后若 loss 或速度明显变化，可隔离 long-short sliding window pattern 的当前贡献；上一轮失败只是 .75 pod 缺 kubectl。 | new | 脚本已修复 .75 direct 执行路径，应立即补齐这个 README top10 缺口。 |
| readme-top10-polar-express-off-rerun1 | Polar Express stability sample | polar_express_off 的 10.8258 loss 若可复现，则 Polar Express/Muon 子项应排在当前 top10 前列。 | new | 当前最强单样本信号，需要排除偶然发散或实现替代过强。 |
| readme-top10-eos-alignment-off-rerun1 | EoS alignment stability sample | 关闭 EoS batch alignment 若再次得到 nan 或显著恶化，可确认该数据排布技巧在当前 root 中是强贡献项。 | new | 已有结果为 nan，但异常信号应至少复核一次。 |
| readme-top10-residual-decay-off | Ablate residual decay | 关闭 residual stream exponential decay 初始化后，可判断该 README 技巧是否在当前 root 中仍有独立贡献。 | new | 脚本已有可逆分支，适合作为补足 architecture/initialization family 排名的低风险单变量实验。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:15:21Z: codex-1780564321617-c96ecaa6

- Trigger: 1 run(s) finished
- Summary: 本轮确认 `.75` 上 polar_express_off_rerun1 失败为环境问题：脚本调用 `python` 时命令不存在，未开始有效 ablation。当前有效因果信号仍包括 polar_express_off 单样本强退化、qk_norm_off 中等退化、value/bigram 稳定退化，以及 eos_alignment_off 的 nan 异常信号；long_window_off 本地 fallback 还在采集中。
- Goal progress: README 历史先验已建立，当前代码已覆盖多数 README 技巧的单变量 ablation。缺口是 polar/eos 等强异常信号的稳定性样本、long-window/YaRN 结果、以及 queued 中的 block3 skip/cautious WD/qk stability。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：远端执行时自动选择 PYTHON_BIN/python/python3；variant 生成、结果收集和解析都使用该解释器；并发训练检测扩展到 python3/python3.x 进程。未修改 train_gpt.py。
- Suggested experiments: 2
- Pending result runs: readme-top10-polar-express-off-rerun1-1780564261-a8d9da97
- Linked experiment ids: readme-top10-polar-express-off-rerun1
- Input code commits: 25a88c3c2c69566386824c85de2b934c0918ff63

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-polar-express-off-rerun2-py3 | Polar Express py3 rerun | 若修复 python/python3 启动问题后 polar_express_off 仍显著发散，可确认 Polar Express 是当前 root 的强因果贡献项。 | new | 上一条 polar stability sample 只因 `.75` 缺 `python` 失败；脚本已修复，优先补有效复跑。 |
| readme-top10-residual-decay-off | Ablate residual decay | 关闭 residual stream exponential decay 初始化后，可判断该 README 技巧在当前 root 中是否仍有独立贡献。 | new | 不与当前 running/queued 项重复，脚本已有可逆分支，可补 architecture/initialization family 排名证据。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:20:04Z: codex-1780564621724-3cf00d68

- Trigger: 2 run(s) finished
- Summary: 当前最强有效因果信号依次是 eos_alignment_off 的 nan 异常、polar_express_off 单样本发散、value_embeds_off 双样本稳定退化、bigram_off 双样本稳定退化、long_window_off 单样本退化、qk_norm_off 单样本中等退化。batch_schedule_constant_final 降低 loss 但显著变慢，应单独按速度/预算收益评估。
- Goal progress: README 历史先验已建立，当前 ablation 已覆盖大多数 top10 技巧。新补齐了 long_window_off 的有效结果，但 polar/eos/long-window/qk_norm 仍需要稳定性样本；现有队列已覆盖 eos、qk_norm、block3 skip、cautious WD、residual decay。
- Code changes: no; 本轮未修改代码；确认当前 run_readme_ablation.sh 语法检查通过。新增 dirty 结果来自 long_window_off 运行落盘，不是代码改动。
- Suggested experiments: 2
- Pending result runs: readme-top10-long-window-off-local-fallback-1780564261-5a299c21, readme-top10-polar-express-off-rerun2-py3-1780564561-01847a2b
- Linked experiment ids: readme-top10-long-window-off-local-fallback, readme-top10-polar-express-off-rerun2-py3
- Input code commits: 25a88c3c2c69566386824c85de2b934c0918ff63, 969df08153d241f6142fa1c7249fb41dcebf5b68

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-polar-express-off-local-rerun3 | Polar Express local stability | 若在 local/.72 直接执行时 polar_express_off 仍显著发散，则可确认 Polar Express 是当前 root 的强因果贡献项，而非 .75 环境噪声。 | new | .75 两次复跑分别失败于 python 缺失和 tar 同步，均未产生训练证据；应先用 local/.72 获取有效稳定性样本。 |
| readme-top10-long-window-off-clean-rerun1 | Long window clean rerun | 若 long_window_off 再次带来约 +0.02 val_loss 退化，则 long-short sliding window/FA3 family 在当前 top10 中应排在 bigram 之后、qk_norm 之前。 | new | 上一条 long_window_off 已有有效 final_result，但 Arthur run 状态因旧脚本后处理语法错误标 failed；需要 clean rerun 给队列一个干净成功样本。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:27:06Z: codex-1780564921761-e3f3c067

- Trigger: 1 run(s) finished
- Summary: 当前有效证据仍以 eos_alignment_off 的 nan、polar_express_off 单样本发散、value_embeds_off 和 bigram_off 双样本退化、long_window_off 单样本退化、qk_norm_off 单样本退化为主；本轮失败均是执行环境问题，不应计入 ablation 结论。
- Goal progress: README 历史先验已建立，当前代码已覆盖多数候选优化的可逆 ablation。缺口是 polar_express_off 和 long_window_off 的干净稳定性样本；EoS、QK、block3 skip、cautious WD、residual decay 已在现有队列中覆盖。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：训练 launcher 先用 torchrun，缺失时退到 python -m torch.distributed.run；同时让 logs 不存在时的 find 不再打断后处理。未修改 train_gpt.py。
- Suggested experiments: 2
- Pending result runs: readme-top10-polar-express-off-local-rerun3-1780564861-f7099cc6
- Linked experiment ids: readme-top10-polar-express-off-local-rerun3
- Input code commits: e52e0f83a773c6f353b915129a917bc9591b8bf3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-polar-express-off-local-pod72-rerun4 | Polar Express pod72 stability | 若在已验证可用的 .72 pod 上 polar_express_off 再次显著发散，则 Polar Express/Muon 子项可确认为当前 root 的最强因果贡献之一。 | new | 本轮 local direct 因 host 缺 torchrun 失败，.75 又有环境问题；.72 pod 是当前最可靠路径。 |
| readme-top10-long-window-off-local-pod72-rerun2 | Long window pod72 clean rerun | 若 long_window_off 在 .72 pod 上再次产生约 +0.02 val_loss 退化，则 long-window/FA3 window family 应进入当前 top10 的中上位。 | new | 已有 long_window_off final_result=3.2969，但 run 状态被旧后处理错误标 failed；当前 .75 clean rerun 未进训练。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:32:05Z: codex-1780565281106-7d758e6c

- Trigger: 1 run(s) finished
- Summary: 最新 long_window_off clean rerun 在 .75 上失败于环境/同步问题，未产生训练证据；现有有效证据不变：polar_express_off 单样本 val_loss=10.8258 最强但需复跑，eos_alignment_off 为 nan 强异常信号，value_embeds_off 与 bigram_off 有双样本稳定退化，long_window_off 单样本 val_loss=3.2969 约 +0.02，qk_norm_off 单样本中等退化。
- Goal progress: README 历史先验已建立，当前代码已覆盖多数候选优化的可逆 ablation。缺口仍是 polar_express_off、long_window_off、eos_alignment_off、qk_norm_off 的稳定性样本，以及 block3 skip、cautious WD、residual decay 的未完成 queued 结果；这些已经在现有队列中覆盖，优先使用 .72 pod，暂不把 .75 失败计入因果排名。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：只有 logs 目录存在时才用 find 回退查找最新训练日志，避免远端训练在创建 logs 前失败时，set -euo pipefail 下的 find 错误掩盖真实根因。已通过 bash -n 和无 logs 目录复现检查。
- Suggested experiments: 0
- Pending result runs: readme-top10-long-window-off-clean-rerun1-1780564861-9718a038
- Linked experiment ids: readme-top10-long-window-off-clean-rerun1
- Input code commits: e52e0f83a773c6f353b915129a917bc9591b8bf3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:41:21Z: codex-1780565641362-4e1ff892

- Trigger: 1 run(s) finished
- Summary: polar_express_off 已有两条有效训练证据：一次 val_loss=10.8258，一次 val_loss=nan，说明关闭 Polar Express 会导致发散级退化，是当前最强因果信号之一。long_window_off 仍只有一条有效样本 val_loss=3.2969；本轮 .75 rerun 失败于缺 kernels 依赖，不计入因果证据。
- Goal progress: README 历史先验已建立，当前代码 ablation 已覆盖多数 top10 候选。当前最强证据层级为 Polar Express/Muon 子项、EoS alignment 的 nan、value embeddings 双样本退化、bigram 双样本退化、long-window 单样本退化、QK norm 单样本退化。缺口是 long-window 稳定性样本，以及已 queued 的 EoS/QK/block3/cautious WD/residual decay 结果。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh：在生成 variant 后、启动 torchrun 前增加 Python 依赖预检；若 torch/triton/kernels import 失败，仅尝试 pip install kernels 后再验证，避免 .75 因缺 kernels 在 import 阶段空跑。未修改 train_gpt.py。
- Suggested experiments: 1
- Pending result runs: readme-top10-long-window-off-local-pod72-rerun2-1780565581-4b1f96e1
- Linked experiment ids: readme-top10-long-window-off-local-pod72-rerun2
- Input code commits: bcebf537dca1d74444501e30de21d01c734881d2

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-long-window-off-depfix-rerun3 | Long window depfix rerun | 若依赖预检修复后 long_window_off 再次得到约 3.296 左右的退化，则 long-window/FA3 window family 的当前贡献可从单样本升级为稳定信号。 | new | long_window_off 仍缺干净稳定性样本；最新失败是 .75 缺 kernels，启动器已最小修复。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:43:28Z: codex-1780566119822-b1a685d8

- Trigger: batch finished with results pending commit
- Summary: 当前 strongest evidence：polar_express_off 两次有效训练均发散或近发散；eos_alignment_off 有 nan 强异常；value_embeds_off、bigram_off 有双样本稳定退化；long_window_off 与 qk_norm_off 仍是单样本退化信号。batch_schedule_constant_final 降低 loss 但明显变慢，应单独按预算/速度权衡。
- Goal progress: README historical prior 已建立，当前 ablation 已覆盖多数 top10 候选。主要缺口是 long_window_off 的干净稳定性样本，以及 queued 中尚未完成的 EoS/QK/block3 skip/cautious WD/residual decay 证据；现有队列已覆盖这些问题。
- Code changes: no; 本轮未修改代码；仅核对结果表、历史 ranking、最近 Arthur 分析与启动脚本状态。
- Suggested experiments: 0
- Pending result runs: readme-top10-polar-express-off-local-pod72-rerun4-1780565581-e79bb50f
- Linked experiment ids: readme-top10-polar-express-off-local-pod72-rerun4
- Input code commits: bcebf537dca1d74444501e30de21d01c734881d2

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:48:50Z: codex-1780566421405-e1362529

- Trigger: 1 run(s) finished
- Summary: polar_express_off 已有三条有效反证：val_loss=10.8258、nan、nan，关闭 Polar Express 会导致发散级退化；当前 provisional 强信号依次包括 Polar Express/Muon 子项、EoS alignment nan、value embeddings 双样本退化、bigram 双样本退化、long-window 单样本退化、QK norm 单样本退化。batch_schedule_constant_final 降低 loss 但显著变慢，应按速度/预算单独评估。
- Goal progress: README historical prior 已建立，当前代码 ablation 已覆盖多数 top10 候选。主要缺口仍是 long_window_off、EoS alignment、QK norm 的稳定性样本，以及 block3 skip、cautious WD、residual decay 的待完成结果；这些已经在现有 .72/local 队列中覆盖，当前不应新增重复实验。
- Code changes: no; 本轮未修改代码；仅核对并归纳新产生的 polar_express_off 结果文件和汇总 CSV。
- Suggested experiments: 0
- Pending result runs: readme-top10-polar-express-off-local-rerun3-1780566227-cd9f513e
- Linked experiment ids: readme-top10-polar-express-off-local-rerun3
- Input code commits: ced53fe0c6a6fa4432713e884ccc4a135adb6404

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T09:53:24Z: codex-current

- Trigger: 1 run(s) finished
- Summary: 新完成的 `readme_top10_polar_express_off_rerun2_py3` 又得到 `val_loss=10.8258`，polar_express_off 现在有四条有效反证：两次 10.8258、两次 nan。关闭 Polar Express 会稳定导致发散级退化，是当前 root 上最强因果贡献信号。
- Goal progress: README historical prior 已建立，当前 ablation 已覆盖多数 top10 候选。当前证据层级为 Polar Express/Muon 子项最强，EoS alignment nan 次强，value embeddings 与 bigram hash embedding 有双样本稳定退化，long-window 和 QK norm 仍需稳定性样本。现有队列已经覆盖 long-window、EoS、QK、block3 skip、cautious WD、residual decay 等缺口，本轮不新增重复实验。
- Code changes: no; 未修改训练代码或运行脚本。仅记录本轮分析；结果表和汇总文件由刚完成的 run/collect_results 产生。
- Suggested experiments: 0
- Pending result runs: readme-top10-polar-express-off-rerun2-py3-1780566541-849543fd
- Linked experiment ids: readme-top10-polar-express-off-rerun2-py3
- Input code commits: c27f05c1ba6468f04a6c4d0a0aba8f11c0765e42

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/readme_top10_ablation_results.csv`
- `experiments/results/readme_top10_readme_top10_polar_express_off_rerun2_py3.json`
- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

## 2026-06-04T09:54:28Z: codex-1780566721510-301a8c5a

- Trigger: 1 run(s) finished
- Summary: polar_express_off 现在有四条有效反证：10.8258、nan、nan、10.8258。关闭 Polar Express 会稳定导致发散级退化，是当前 root 上最强因果贡献信号；EoS alignment 有 nan 强异常；value embeddings 和 bigram hash embedding 有双样本稳定退化；long_window_off 与 qk_norm_off 仍是单样本退化信号。
- Goal progress: README historical prior 已建立，当前 ablation 已覆盖多数 top10 候选。缺口仍是 long-window、EoS、QK、block3 skip、cautious WD、residual decay 的稳定或首样本证据；这些已在现有 queued 实验中覆盖。batch_schedule_constant_final 降低 loss 但显著变慢，应按速度/预算单独评估，不直接混入等预算 top10。
- Code changes: no; 未修改训练代码或运行脚本；仅追加 experiments/arthur/idea_result_links.md 的本轮分析记录。最新结果文件和汇总 CSV/JSON 来自刚完成的 run/collect_results。
- Suggested experiments: 0
- Pending result runs: readme-top10-polar-express-off-rerun2-py3-1780566541-849543fd
- Linked experiment ids: readme-top10-polar-express-off-rerun2-py3
- Input code commits: c27f05c1ba6468f04a6c4d0a0aba8f11c0765e42

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

## 2026-06-04T09:59:12Z: codex-current

- Trigger: 1 run(s) finished
- Summary: 新完成的 `readme_top10_long_window_off_local_pod72_rerun2` 得到 `val_loss=3.2975`、`train_time_min=1.2786`，与已有 `long_window_off` 样本 `val_loss=3.2969` 一致。关闭 long-window/FA3 window family 在当前 root 上稳定损害 loss 约 +0.018，证据从单样本升级为双样本稳定退化。
- Goal progress: README historical prior 已建立，当前 ablation 已覆盖多数 top10 候选。当前强证据层级为 Polar Express/Muon 子项最强，EoS alignment nan 强异常，value embeddings 与 bigram hash embedding 双样本退化，long-window 双样本退化，QK norm 单样本退化。剩余缺口是 EoS/QK 的稳定样本，以及 block3 skip、cautious WD、residual decay 等现有 queued 实验的首样本证据。
- Code changes: no; 本轮未修改训练代码或运行脚本。仅追加本分析记录；最新 long-window 结果文件和汇总 CSV/JSON 来自刚完成的 run/collect_results。
- Suggested experiments: 0
- Pending result runs: readme-top10-long-window-off-local-pod72-rerun2-1780566901-8d5a8340
- Linked experiment ids: readme-top10-long-window-off-local-pod72-rerun2
- Input code commits: c6fffd7ee21c5de36573f6fccdd486a2fde355e3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/readme_top10_ablation_results.csv`
- `experiments/results/readme_top10_readme_top10_long_window_off_local_pod72_rerun2.json`
- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

## 2026-06-04T10:00:28Z: codex-1780567082027-81beb7c4

- Trigger: 1 run(s) finished
- Summary: long_window_off 新样本 val_loss=3.2975，与已有 3.2969 一致；关闭 long-window/FA3 window family 稳定损害当前 root 的 loss。当前最强因果证据仍是 Polar Express/Muon 子项，之后是 EoS alignment nan、value embeddings 双样本退化、bigram hash embedding 双样本退化、long-window 双样本退化、QK norm 单样本退化。
- Goal progress: README record-history delta 先验已建立，当前代码 ablation 已覆盖多数 top10 候选。缺口主要是 EoS/QK 的稳定性样本，以及 block3 skip、cautious WD、residual decay 等 queued 实验的首样本证据；这些已有队列覆盖，当前不需要重复新增。
- Code changes: no; 未修改训练代码或运行脚本；仅追加 experiments/arthur/idea_result_links.md 的本轮分析记录。结果 CSV/JSON 由刚完成的 run/collect_results 产生。
- Suggested experiments: 0
- Pending result runs: readme-top10-long-window-off-local-pod72-rerun2-1780566901-8d5a8340
- Linked experiment ids: readme-top10-long-window-off-local-pod72-rerun2
- Input code commits: c6fffd7ee21c5de36573f6fccdd486a2fde355e3

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:08:54Z: codex-1780567441281-a1f3b7c2

- Trigger: 1 run(s) finished
- Summary: 当前最强因果证据仍是 Polar Express/Muon 子项：关闭后出现 10.8258 或 nan。其次是 EoS alignment 单样本 nan、value embeddings 双样本稳定退化、bigram hash embedding 双样本稳定退化、long-window 三样本稳定退化。QK norm、MTP、XSA、smear 仍主要是单样本信号；zero projection init、embedding skip、PKO 在当前短跑上未显示明确损失惩罚。
- Goal progress: README record-history delta 先验已建立，当前 ablation 已覆盖大部分历史 top10 候选。主要缺口是 EoS/QK 稳定样本，以及 block3 skip、cautious WD、residual decay 的首样本证据；这些已有队列覆盖。batch schedule 现有结果 val_loss 很低但训练明显变慢，且 constant_final 改变了 token 预算，因此需要一个更干净的等均值 batch ablation。
- Code changes: yes; 修改 experiments/arthur/run_readme_ablation.sh，新增 batch_schedule_constant_mean ablation：将前三个 scheduled stages 的 batch 从 8/16/24 调为 16/16/16，近似保持 scheduled training token 预算，用于隔离 batch schedule 形状本身。已通过 bash -n 检查。
- Suggested experiments: 1
- Pending result runs: readme-top10-long-window-off-local-fallback-1780567261-d417d66f
- Linked experiment ids: readme-top10-long-window-off-local-fallback
- Input code commits: 82bff4ccf4a87f787dc001f197cd4541be0f4f86

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-batch-schedule-constant-mean-local | Mean batch schedule ablation | 如果 batch size schedule 本身有效，那么在近似保持三段 scheduled token 总量的 16/16/16 常量 batch 下，loss 或 time/target tradeoff 应劣于当前 8/16/24 schedule；这比 constant_final 更少混入额外 token 预算。 | new | 现在跑是因为现有 batch_schedule_constant_final 结果 val_loss=3.2346 但 step_avg≈80.85ms，不能直接作为 README batch schedule 的正反证。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

## 2026-06-04T10:20:22Z: codex-1780567982051-0da1b9b7

- Trigger: 1 run(s) finished
- Summary: batch_schedule_constant_mean_local 有效完成但未达标：val_loss=3.3004, train_time_min=1.2898, step_avg_ms=56.08。它提供了 batch size ramp 的首个干净负向 ablation 证据。
- Goal progress: README 历史先验已建立，当前最强因果证据仍是 Polar Express/Muon 子项，其次是 EoS alignment nan、value embeddings、bigram hash embedding、long-window、batch schedule、QK norm。缺口是 batch/QK/EoS 稳定性样本，以及 block3 skip、cautious WD、residual decay 的首样本证据。
- Code changes: no; 未修改训练代码或运行脚本；仅追加 Arthur 分析日志。结果 CSV/JSON/summary 是刚完成 run 的落盘更新。
- Suggested experiments: 1
- Pending result runs: readme-top10-batch-schedule-constant-mean-local-1780567741-d44e4079
- Linked experiment ids: readme-top10-batch-schedule-constant-mean-local
- Input code commits: 09d7ea1e2ae6cfa4a68703447f34166f7d97191b

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-batch-schedule-constant-mean-rerun1 | Mean batch schedule stability | 如果 16/16/16 等均值常量 batch 再次得到约 3.30 loss 且无速度收益，则 batch size ramp 可作为当前 top10 的稳定因果贡献项。 | new | 首个 constant_mean 样本有效但只有一次；复跑可确认这是 batch ramp 的稳定贡献，而非单次方差。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:26:27Z: codex-1780568641588-1dc86fbe

- Trigger: 1 run(s) finished
- Summary: long_window_off 新样本 val_loss=3.2954、target_met=false，强化了 long-window/FA3-window family 的稳定负向因果证据。当前最强证据仍是 Polar Express/Muon 子项，关闭后多次出现 10.8258 或 nan；其次是 EoS alignment 单样本 nan、value embeddings 双样本约 3.312-3.315、bigram 双样本约 3.299-3.302、batch_schedule_constant_mean 单样本 3.3004，以及 long_window_off 多样本约 3.295-3.297。
- Goal progress: README record-history delta 先验已建立，当前代码 ablation 已覆盖大多数历史 top10。缺口仍是 EoS/QK/batch schedule 的稳定性样本，以及 block3 skip、cautious WD、residual decay 的首样本；这些实验已经在现有队列中，当前无需新增重复实验。
- Code changes: no; 未修改代码；本轮只分析刚完成的 long_window_off 结果。
- Suggested experiments: 0
- Pending result runs: readme-top10-long-window-off-clean-rerun1-1780568461-e881b202
- Linked experiment ids: readme-top10-long-window-off-clean-rerun1
- Input code commits: 78451a8f43690877e4cc76aa8232b4cbee3b8534

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:30:56Z: codex-1780569001906-feae00f8

- Trigger: 1 run(s) finished
- Summary: long_window_off 新样本 val_loss=3.2962，第四次稳定未达 3.28 目标，强化 long-window/FA3-window family 的正向因果证据；当前排序上它应低于 Polar Express、EoS alignment、value embeddings、bigram hash embedding、batch schedule。
- Goal progress: README record-history delta 先验已建立，当前 ablation 已覆盖多数 README top10 候选。缺口仍是 EoS/QK/batch schedule 的稳定样本，以及 block3 skip、cautious WD、residual decay 的首样本；这些已经在现有队列中，不需要新增重复实验。
- Code changes: no; 未修改代码；本轮只分析 readme-top10-long-window-off-depfix-rerun3 的落盘结果。
- Suggested experiments: 0
- Pending result runs: readme-top10-long-window-off-depfix-rerun3-1780568821-0dddaf72
- Linked experiment ids: readme-top10-long-window-off-depfix-rerun3
- Input code commits: 793263f047d2291000b6fb5c94503d2e6cd3d551

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:35:58Z: codex-1780569241330-55167916

- Trigger: 1 run(s) finished
- Summary: polar_express_off 现在有 5 条有效反事实证据：两次 val_loss=10.8258，三次 val_loss=nan。关闭 Polar Express 会稳定导致发散级退化，是当前 root 上最强因果贡献信号。当前较强证据层级为 Polar Express/Muon 子项、EoS alignment nan、value embeddings 双样本退化、bigram hash embedding 双样本退化、batch_schedule_constant_mean 单样本退化、long-window 多样本退化、QK norm 单样本退化。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖大多数历史 top10 候选。主要缺口仍是 EoS/QK/batch schedule 的稳定性样本，以及 block3 skip、cautious WD、residual decay 的首样本证据；这些已在现有 queued 实验中覆盖，当前不需要新增重复实验。
- Code changes: no; 未修改代码；本轮只分析刚完成的 polar_express_off_rerun1 结果。结果 CSV/JSON 已由运行落盘，等待 Arthur 提交。
- Suggested experiments: 0
- Pending result runs: readme-top10-polar-express-off-rerun1-1780569061-41667276
- Linked experiment ids: readme-top10-polar-express-off-rerun1
- Input code commits: e933bfc48111680094f688fe928a7ba7095652d9

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:42:29Z: codex-1780569541143-de051aeb

- Trigger: 1 run(s) finished
- Summary: EoS alignment off 新样本 val_loss=nan、target_met=false，强化 EoS 对齐是当前 top10 候选之一的强因果证据。当前最强仍是 Polar Express/Muon 子项；其次包括 EoS alignment、value embeddings、bigram hash embedding、batch schedule constant mean、long-window family、QK norm 等，但部分候选还缺首样本或稳定样本。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖大多数候选。主要缺口是把 README 第10项中的 max document count 从 EoS alignment 中拆开验证，以及等待 block3 skip、cautious WD、residual decay、QK/batch/EoS 稳定性样本完成。
- Code changes: yes; 在 experiments/arthur/run_readme_ablation.sh 新增 max_doc_count_off 可逆 ablation 分支，将 TRAIN_MAX_NUM_DOCS 置空以回到旧启发式 max document count；未修改 train_gpt.py。
- Suggested experiments: 1
- Pending result runs: readme-top10-eos-alignment-off-local-1780569361-b4fd4c95
- Linked experiment ids: readme-top10-eos-alignment-off-local
- Input code commits: 85606e1b3682c9766a2d54d99047f2494ca97f91

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-max-doc-count-off-local | Ablate max document count table | 单独关闭 TRAIN_MAX_NUM_DOCS 表会判断 README 的 EoS-aligned batches and max document length 记录中，max document count 是否独立贡献 loss 或速度，而不是把全部 credit 归给 EoS alignment。 | new | 现有 EoS ablation 已两次 nan，但它只关闭 align_to_bos；这个实验隔离同一 README 条目里的 max document count 变量。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:49:21Z: codex-1780570021519-7a159655

- Trigger: 1 run(s) finished
- Summary: batch_schedule_constant_final_local_fixed 完成：val_loss=3.2342, target_met=true，但 train_time_min=1.8624、step_avg_ms=80.97，明显慢于当前 root/clean ablation 的约 1.27-1.29 分钟。该结果说明更大固定 batch/更多文档设置能降低 loss，但因同时改动 batch schedule 和 TRAIN_MAX_NUM_DOCS，不能作为干净的 batch schedule 因果证据。
- Goal progress: README 历史先验已建立，当前代码 ablation 已覆盖多数 top10 候选。强证据仍是 Polar Express/Muon 子项、EoS alignment、value embeddings、bigram hash embedding、long-window family、batch_schedule_constant_mean 单样本和 QK norm 单样本。缺口仍是 batch_schedule_constant_mean 稳定性、max document count 拆分、block3 skip、cautious WD、residual decay 首样本，以及 QK/EoS 稳定样本；这些已经在现有队列中。
- Code changes: no; 未修改代码；本轮只分析刚完成的 batch_schedule_constant_final_local_fixed 结果。结果 CSV/JSON/comparison 由运行落盘，等待 Arthur 提交。
- Suggested experiments: 0
- Pending result runs: readme-top10-batch-schedule-constant-final-local-fixed-1780569781-3841b63c
- Linked experiment ids: readme-top10-batch-schedule-constant-final-local-fixed
- Input code commits: 0e80b6eec05eb9788ab0ccbf51dcc167add4b6eb

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:54:21Z: codex-1780570381079-75496863

- Trigger: 1 run(s) finished
- Summary: long_window_off 现在有 6 条有效反事实样本，val_loss 约 3.2954-3.2989，均未达 3.28，说明关闭长窗口会稳定退化；最新样本 val_loss=3.2989 强化该结论。当前最强因果证据仍是 Polar Express/Muon 子项，其次是 EoS alignment、value embeddings、bigram hash embedding、batch_schedule_constant_mean、long-window family、QK norm 等。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖多数 top10 候选。缺口仍是 block3 skip、cautious weight decay、residual decay 的首样本，以及 QK/EoS/batch schedule/max document count 的稳定或拆分样本；这些已经在现有 queued 实验中覆盖，先让队列继续推进。
- Code changes: no; 未修改代码；本轮只分析刚完成的 readme-top10-long-window-off 结果。
- Suggested experiments: 0
- Pending result runs: readme-top10-long-window-off-1780570201-001417aa
- Linked experiment ids: readme-top10-long-window-off
- Input code commits: a4ecdab4701ee642a6b2ed4b263807306605827f

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T10:59:35Z: codex-1780570681655-4f16f7b8

- Trigger: 1 run(s) finished
- Summary: batch_schedule_constant_mean 已有两个干净样本，val_loss=3.3004 和 3.3003，均未达 3.28，支持 batch size schedule 是稳定有效的 README 优化项；batch_schedule_constant_final 虽达标但存在 batch/max-doc 混杂，不作为干净因果证据。
- Goal progress: README 历史先验已建立，当前 ablation 已覆盖多数 top10 候选。强证据包括 Polar Express/Muon 子项、EoS alignment、value embeddings、bigram hash embedding、long-window family、batch schedule、QK norm 等；缺口仍是 max document count 拆分、block3 skip、cautious weight decay、residual decay 首样本，以及若干单样本候选的稳定性确认。现有 queued 实验已覆盖这些缺口。
- Code changes: no; 未修改代码；本轮只分析刚完成的 batch_schedule_constant_mean_rerun1 结果。
- Suggested experiments: 0
- Pending result runs: readme-top10-batch-schedule-constant-mean-rerun1-1780570501-ac57177c
- Linked experiment ids: readme-top10-batch-schedule-constant-mean-rerun1
- Input code commits: 51544dc4d8d1c726a5201ceea3eed31e1dd5ef11

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T11:05:30Z: codex-1780571041971-bc27641e

- Trigger: 1 run(s) finished
- Summary: 本轮新完成的 batch_schedule_constant_final_local target_met=true，但属于更慢且混杂的探索结果；不提升 batch schedule 的干净因果证据等级。当前强证据仍是 Polar Express/Muon 子项最强，其次是 EoS alignment nan、value embeddings、bigram hash embedding、batch schedule mean、long-window family、QK norm 单样本。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖大多数 top10 候选。剩余缺口是 max document count 拆分、block3 skip、cautious WD、residual decay 首样本，以及 QK/EoS 稳定性样本；这些已经在现有 queued 实验中覆盖，先等待队列推进。
- Code changes: no; 未修改代码；本轮只分析 readme-top10-batch-schedule-constant-final-local 新结果。运行产物已由实验脚本落盘，等待 Arthur 提交。
- Suggested experiments: 0
- Pending result runs: readme-top10-batch-schedule-constant-final-local-1780570801-31aaa546
- Linked experiment ids: readme-top10-batch-schedule-constant-final-local
- Input code commits: 06da2a1a99a4405a6eb4bf41d53988a8f0670338

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T11:11:21Z: codex-1780571341287-17ef1a66

- Trigger: 1 run(s) finished
- Summary: cautious_wd_off 完成 1380/1380，val_loss=3.2821、train_time_min=1.28785、target_met=false。该结果支持 cautious weight decay 有正向贡献，但当前效应很小，低于 value/bigram/long-window/QK 等强候选，暂不能凭单样本进入 top10。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖大多数候选。本轮补齐了 cautious WD 首样本；剩余关键缺口仍是 max document count 拆分、block3 skip、residual decay 首样本，以及 QK/EoS 等稳定性样本，其中多数已在现有队列中。
- Code changes: no; 未修改代码；本轮只分析 readme-top10-cautious-wd-off 运行结果。运行产物已由实验脚本落盘，等待 Arthur 提交。
- Suggested experiments: 1
- Pending result runs: readme-top10-cautious-wd-off-1780571162-79f9ff94
- Linked experiment ids: readme-top10-cautious-wd-off
- Input code commits: f5334f7fd719fb03939cb81c7ed3d5b37d382f98

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-cautious-wd-off-rerun1 | Cautious WD stability sample | 第二个 cautious_wd_off 样本将判断 3.2821 的轻微退化是否稳定，还是接近随机波动；这决定 cautious WD 是否只作为边界候选。 | new | cautious WD 首样本只比阈值差 0.0021，证据不足以定级；优先级低于仍缺首样本的 max-doc/block3/residual。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T11:17:46Z: codex-1780571761227-f3a85e91

- Trigger: 1 run(s) finished
- Summary: max_doc_count_off 产生了有效结果：val_loss=3.2764、target_met=true、train_time_min=1.2953。该结果暂时反驳“当前 TRAIN_MAX_NUM_DOCS table 明显有益”的假设，但单样本不足以定论。
- Goal progress: README 历史先验已建立，当前 ablation 已覆盖多数候选。强因果证据仍集中在 Polar Express/Muon、EoS alignment、value embeddings、bigram hash、batch schedule、long windows、QK norm 等；max document count 现在从缺口变为反常/待复验项。block3 skip、residual decay、QK/EoS 稳定样本等仍在现有队列中。
- Code changes: no; 未修改代码；本轮只分析 readme-top10-max-doc-count-off-local 结果。运行产物已落盘，等待 Arthur 提交。
- Suggested experiments: 1
- Pending result runs: readme-top10-max-doc-count-off-local-1780571521-44621830
- Linked experiment ids: readme-top10-max-doc-count-off-local
- Input code commits: fc7c93d284f2a1c1ee4ed91fbe961f1c93dc054c

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-max-doc-count-off-rerun1 | Max doc count stability sample | 第二个 max_doc_count_off 样本将验证关闭 TRAIN_MAX_NUM_DOCS table 后仍能达标且不退化；若稳定，则 max document count table 在当前代码中应降级为无效或边界候选。 | new | 首样本与历史先验方向相反，而且 Arthur 状态误标为 failed；需要干净复跑来决定是否保留该优化项。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T11:22:26Z: codex-1780572061775-316485d6

- Trigger: 1 run(s) finished
- Summary: max_doc_count_off 两个有效样本分别为 val_loss=3.2764 和 3.2788，均 target_met=true；当前代码下没有看到 TRAIN_MAX_NUM_DOCS table 的正向因果贡献，暂时从 top10 强候选降级为边界/无效项。
- Goal progress: README record-history delta 历史先验已建立，当前 ablation 已覆盖大多数候选。强因果证据仍集中在 Polar Express/Muon、EoS alignment、value embeddings、bigram hash embedding、batch schedule mean、long windows、QK norm 等；max document count 已从缺口变成反证项。剩余关键缺口是 block3 skip 和 residual decay 首样本，以及 QK/EoS/cautious WD 稳定性样本，这些已经在现有 queued 实验中覆盖。
- Code changes: no; 未修改代码；本轮只分析 readme-top10-max-doc-count-off-rerun1 新结果。
- Suggested experiments: 0
- Pending result runs: readme-top10-max-doc-count-off-rerun1-1780571881-195fb678
- Linked experiment ids: readme-top10-max-doc-count-off-rerun1
- Input code commits: 0e7e90a2c6e9b14ff7bf0d323257c30f430bca77

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

## 2026-06-04T11:30:56Z: codex-1780572542015-d83be8a8

- Trigger: 1 run(s) finished
- Summary: 当前强因果证据仍集中在 Polar Express/Muon、value embeddings、bigram hash、batch schedule mean、long windows、QK norm 等；block3 skip 首样本接近阈值但不强。
- Goal progress: 历史先验已建立，当前 ablation 已覆盖 skip family 两个拆分项。剩余缺口主要是 residual decay 首样本，以及 QK/EoS/cautious WD/block3 skip 稳定性样本。
- Code changes: no; 未修改训练源码；只在 experiments/arthur/idea_result_links.md 追加本轮分析。运行结果文件由实验脚本生成。
- Suggested experiments: 1
- Pending result runs: readme-top10-block3-skip-off-1780572181-fd70e2f0
- Linked experiment ids: readme-top10-block3-skip-off
- Input code commits: b7bdb28ce42e2fd54362a05644539217feb924ce

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |
| readme-top10-block3-skip-off-rerun1 | Block3 skip stability sample | 第二个 block3_skip_off 样本将判断 3.2798 的边界结果是否稳定；若仍 target_met 且接近 baseline，则 block3 skip 当前因果贡献应降级。 | new | block3 skip 是历史 skip-family 高先验项，但首样本只在阈值边缘，不能单样本定级。 |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`


## 2026-06-04T11:35:40Z: codex-1780572841641-b6f32b95

- Trigger: 1 run(s) finished
- Summary: readme_top10_eos_alignment_off_rerun1 完成 1380/1380 后 val_loss=nan、target_met=false；EoS alignment 从异常单样本升级为多样本强证据。当前强因果证据集中在 Polar Express/Muon 子项、EoS alignment、value embeddings、bigram hash embedding、batch schedule mean、long-window family；QK norm 仍需稳定样本，cautious WD/block3 skip 属边界候选，max_doc_count 暂降级为无效或边界项。
- Goal progress: README record-history delta 历史先验已建立，当前代码 ablation 已覆盖大多数 top10 候选。本轮补强了 EoS alignment 稳定性证据；主要缺口仍是 QK norm 稳定性、residual decay 首样本，以及 cautious WD/block3 skip 的边界复验，这些已在现有 queued 实验中覆盖。
- Code changes: no; 未修改代码；本轮只分析新完成的 eos_alignment_off 复跑结果。运行产物已落盘，等待 Arthur 提交。
- Suggested experiments: 0
- Pending result runs: readme-top10-eos-alignment-off-rerun1-1780572661-fb62c7d2
- Linked experiment ids: readme-top10-eos-alignment-off-rerun1
- Input code commits: b74fd3d622a3bd9aaaa90cc504ba14a7355abc2f

### Ideas

| experiment id | title | hypothesis | status at analysis | notes |
| --- | --- | --- | --- | --- |

### Linked Result Files

- `experiments/results/comparison.md`
- `experiments/results/local_reruns.csv`
- `experiments/results/log_results.csv`
- `experiments/results/summary.json`

