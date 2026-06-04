#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD:-modded-nanogpt-repro}"

kubectl get pod "${POD}" -o wide

kubectl exec -i "${POD}" -- bash -s <<'REMOTE'
set -euo pipefail
cd /workspace/modded-nanogpt

echo "workspace=$PWD"
python --version
python - <<'PY'
from pathlib import Path
import torch
import triton

print(f"torch={torch.__version__}")
print(f"triton={triton.__version__}")
print(f"cuda_available={torch.cuda.is_available()}")
print(f"cuda_device_count={torch.cuda.device_count()}")

data = Path("data/fineweb10B")
train = sorted(data.glob("fineweb_train_*.bin"))
val = sorted(data.glob("fineweb_val_*.bin"))
print(f"train_shards={len(train)}")
print(f"val_shards={len(val)}")
if len(train) < 32 or len(val) < 1:
    raise SystemExit("fineweb10B shard set is incomplete")
PY

which torchrun
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
REMOTE
