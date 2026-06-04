# README Top10 Optimization Plan

Goal: identify the top 10 most effective optimization methods listed in README.

Method:
- Use README record-history deltas as the historical prior.
- Split credit across multiple named techniques in the same record.
- Validate current-code effects with safe reversible ablations first.
- Treat historical ranking as prior evidence, not causal proof.

Current historical top 10:

| rank | technique | delta min | delta pct | mentions |
| --- | --- | ---: | ---: | ---: |
| 1 | Modernized architecture: Rotary embeddings, QK-Norm, and ReLU2 | 17.304 | 51.31% | 4 |
| 2 | Muon optimizer | 11.386 | 52.54% | 11 |
| 3 | Zero initialization of projections | 3.550 | 15.92% | 1 |
| 4 | Embedding/block skip connections | 1.944 | 22.22% | 5 |
| 5 | FP8 lm_head, asymmetric rescale, and softcap logits | 1.880 | 33.00% | 8 |
| 6 | Value embeddings | 1.008 | 24.57% | 8 |
| 7 | Flash Attention 3, long-short sliding windows, window warmup, YaRN | 0.555 | 14.06% | 5 |
| 8 | Batch size schedule | 0.104 | 3.97% | 2 |
| 9 | Bigram hash embedding | 0.098 | 5.65% | 2 |
| 10 | EoS-aligned batches and max document length | 0.074 | 2.58% | 2 |

First ablation batch:
- Learnable XSA off
- Smear off
- Partial Key Offset off
- Multi-token prediction off
- Bigram hash embedding off
- Value embeddings off

Deferred ablations need more careful code surgery: MUDD, NorMuon/Polar Express, FA3/window schedule, Cautious Weight Decay, paired heads, and batch/sequence schedules.
