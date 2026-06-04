# Modded-NanoGPT 实验复现记录

日期：2026-06-03 至 2026-06-04

## 目标

对 repo/README 中提到的改进点进行复现：优先复跑当前 checkout 中有可执行脚本的记录，记录本地结果，并与 README 声称结果对比。

完整自动汇总报告见 `experiments/results/comparison.md`，机器可读结果见 `experiments/results/`。

## 环境

- Kubernetes Pod：`modded-nanogpt-repro`
- 节点：`host-172-31-13-72`，Pod IP `172.31.13.72`
- GPU：8 x NVIDIA H200
- Python：3.12.13
- PyTorch：2.11.0+cu130
- CUDA：13.0
- Triton：3.6.0
- 宿主机 repo 路径：`/data/develop/modded-nanogpt`
- Pod 内 repo 路径：`/workspace/modded-nanogpt`

README 官方 timing 基于 8 x H100。本次本地结果来自 8 x H200 和当前 Pod 软件栈，因此 wall-clock 对比只能作为当前环境下的复现参考，不是严格同硬件复现。

## 数据

FineWeb 数据放在 `/data` 挂载盘下：

- 路径：`/data/develop/modded-nanogpt/data/fineweb10B`
- Train shards：32 个，`fineweb_train_000001.bin` 到 `fineweb_train_000032.bin`
- Val shard：`fineweb_val_000000.bin`
- 目录大小：约 6.2G

medium-track 首次完整尝试在 `1625/5960` 后中断，原因是 train shard 数量不足。补齐到 32 个 train shard 后，5960-step medium 复跑可以跑满。

网络下载异常时使用代理：

```bash
https_proxy=http://127.0.0.1:1083
```

## 执行方式

训练在 K8s Pod 内执行，通用命令模板如下：

```bash
kubectl exec modded-nanogpt-repro -- bash -lc '
  cd /workspace/modded-nanogpt &&
  HTTP_PROXY=http://127.0.0.1:1083 \
  HTTPS_PROXY=http://127.0.0.1:1083 \
  http_proxy=http://127.0.0.1:1083 \
  https_proxy=http://127.0.0.1:1083 \
  torchrun --standalone --nproc_per_node=8 <SCRIPT>
'
```

训练任务没有并行运行，避免污染 8 卡 timing。

## 结果汇总脚本

使用以下脚本解析 README、records 历史日志和本地 `logs/`：

```bash
python experiments/collect_results.py
```

生成文件：

- `experiments/results/comparison.md`：完整可读报告
- `experiments/results/readme_records.csv`：README claims 和 reference log 解析结果
- `experiments/results/log_results.csv`：历史日志与本地日志解析结果
- `experiments/results/local_reruns.csv`：本地 completed rerun 分组结果
- `experiments/results/local_vs_readme.csv`：本地复跑与 README 直接对比
- `experiments/results/failed_local_runs.csv`：失败或中断的本地尝试
- `experiments/results/top_techniques.csv`：README 改进点列表
- `experiments/results/summary.json`：汇总计数

最新汇总：

| 项目 | 数量 |
| --- | ---: |
| README records | 102 |
| Parsed log results | 947 |
| Local rerun groups | 5 |
| Failed local attempts | 3 |
| README top techniques | 26 |

## 本地复跑结果

目标 loss：

- Short track：`val_loss <= 3.28`
- Medium track：`val_loss <= 2.92`

| 记录 | track | README # | README min | 本地达标最好 min | 差异 | 达标次数 | 本地最好 val_loss | 日志 |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `current_root_learnable_xsa` | short | 82 | 1.353 | 1.295 | -4.25% | 1/2 | 3.2790 | `logs/818163c0-2996-448f-82e2-302cc2b8b920.txt`; `logs/e9cbdea0-b98c-442d-87fc-918463ef113f.txt` |
| `2024-12-04_ValueEmbed` | short | 14 | 4.410 | 3.903 | -11.49% | 1/1 | 3.2735 | `logs/a1f3f41b-abfe-4012-89fd-7e4defdd8ee5.txt` |
| `2025-11-12_BlockMaskRedundantOp` | medium | 17 | 22.980 | 23.109 | +0.56% | 1/1 | 2.919982 | `logs/000_cb759f2a-2d38-4884-bc01-eeb5703c2e78.txt` |
| `2024-10-14_ModernArch` | short | 5 | 15.200 | n/a | n/a | 0/1 | 3.2939 | `logs/8fec36ab-393f-4389-b773-baebace6c927.txt` |
| `2024-10-10_Muon` | short | 4 | 22.300 | n/a | n/a | 0/1 | 3.3006 | `logs/f34daba5-179a-439b-9809-af4ac20b7d73.txt` |

说明：

- current-root short 记录跑了两次：一次 `val_loss=3.2803`，略高于目标；一次 `val_loss=3.2790`，达标。
- `2024-10-10_Muon` 和 `2024-10-14_ModernArch` 在当前硬件上的时间快于 README，但 loss 未达到 short-track 目标，因此不计为达标复跑。
- medium #17 使用的是 Torch 2.11 兼容副本，不是未修改的历史脚本。

## Medium #17 兼容处理

原始脚本：

```text
records/track_2_medium/2025-11-12_BlockMaskRedundantOp/train_gpt_medium.py
```

在当前 Torch 2.11/FlexAttention 环境下无法直接启动，触发 compiled-autograd/Dynamo 兼容问题。因此创建兼容副本：

```text
experiments/compat/train_gpt_medium_blockmask_torch211.py
```

兼容修改：

- 设置 `torch._dynamo.config.compiled_autograd = False`
- 调整 `_patched_trace_structured` shim 签名，以兼容 Torch 2.11 cache-hit 调用

完成的 medium #17 复跑：

- 日志：`logs/000_cb759f2a-2d38-4884-bc01-eeb5703c2e78.txt`
- 最终 step：`5960/5960`
- 最终 `val_loss`：`2.919982`
- `train_time`：`1,386,526ms`，约 `23.109 min`
- `step_avg`：`232.64ms`
- 峰值显存：allocated `52129 MiB`，reserved `55354 MiB`

README medium #17 声称 `22.98 min`。本地兼容复跑慢约 `0.129 min`，即 `+0.56%`，但达到 `2.92` 目标 loss。

## 失败或中断记录

| 记录 | 类型 | 原因 | 日志 |
| --- | --- | --- | --- |
| `2025-11-12_BlockMaskRedundantOp` | startup failure | 启动后未产生 validation；Torch 2.11 Dynamo/FlexAttention compiled-autograd 不兼容 | `logs/000_5b519ff4-cd22-4d33-99a9-4ed3dfa78efb.txt` |
| `2025-11-12_BlockMaskRedundantOp` | startup failure | 启动后未产生 validation；Torch 2.11 Dynamo/FlexAttention compiled-autograd 不兼容 | `logs/000_86ddb1f2-0d57-4e6b-af85-ce6a3d2de3f6.txt` |
| `2025-11-12_BlockMaskRedundantOp` | partial run | 在 validation step `1625/5960` 后中断；当时数据 shard 不足 | `logs/000_b0d39018-53e5-4a9c-bbe1-0e28e69393d1.txt` |

## README 改进点覆盖情况

README 中解析到 26 个 top techniques 和 102 条历史记录。当前 checkout 中多数历史记录只有日志，没有可执行脚本；只有带 `train*.py` snapshot 的记录以及根目录 `train_gpt.py` 可以直接复跑。

解析后的可用性：

| availability | 数量 |
| --- | ---: |
| `log_available` | 89 |
| `readme_only` | 8 |
| `rerun_completed` | 5 |

逐条记录对比见 `experiments/results/comparison.md`。

## 验证

最终训练后执行过：

```bash
python experiments/collect_results.py
python -m py_compile experiments/collect_results.py
kubectl get pod modded-nanogpt-repro -o wide
kubectl exec modded-nanogpt-repro -- bash -lc 'nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader'
```

检查结果：

- Pod 仍在 `.72` 节点。
- 训练结束后 8 张 H200 均为空闲。
- 没有遗留训练进程。
- 结果汇总脚本通过 Python 语法编译检查。

## 文件变更

- `experiments/collect_results.py`：结果解析和报告生成脚本
- `experiments/compat/train_gpt_medium_blockmask_torch211.py`：medium #17 的 Torch 2.11 兼容复跑脚本
- `experiments/results/*`：生成的 CSV/JSON/Markdown 结果
- `experiments/reproduction_record.md`：本文档

根目录 `train_gpt.py` 中还包含本次复现准备阶段加入的 Flash Attention 3 fallback 修改。
