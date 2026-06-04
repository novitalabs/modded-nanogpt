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

