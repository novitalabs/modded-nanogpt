#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD:-modded-nanogpt-repro}"
TIMEOUT="${BASELINE_TIMEOUT:-45m}"

kubectl exec -i "${POD}" -- bash -s -- "${TIMEOUT}" <<'REMOTE'
set -euo pipefail
timeout_value="$1"
cd /workspace/modded-nanogpt

active_train="$(ps -eo pid,comm,args | awk '/[t]orchrun .*train_gpt.py|[p]ython .*train_gpt.py/ {print}')"
if [[ -n "${active_train}" ]]; then
  echo "existing train_gpt.py process detected:"
  echo "${active_train}"
  exit 3
fi

echo "starting current-root baseline at $(date -Iseconds)"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

timeout "${timeout_value}" torchrun --standalone --nproc_per_node=8 train_gpt.py

latest_log="$(find logs -maxdepth 1 -type f -name '*.txt' -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)"
if [[ -z "${latest_log}" ]]; then
  echo "no training log found after baseline run"
  exit 4
fi

echo "latest_log=${latest_log}"
tail -160 "${latest_log}"
python experiments/collect_results.py

python - "${latest_log}" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(errors="ignore")
matches = re.findall(
    r"step:(\d+)/(\d+)\s+val_loss:([0-9.]+)\s+train_time:([0-9.]+)ms\s+step_avg:([0-9.]+)ms",
    text,
)
if not matches:
    raise SystemExit(f"no validation result found in {path}")

step, total, loss, train_ms, step_avg = matches[-1]
loss_f = float(loss)
train_min = float(train_ms) / 60000.0
print(
    f"final_result log={path} step={step}/{total} "
    f"val_loss={loss_f:.4f} train_time_min={train_min:.4f} step_avg_ms={float(step_avg):.2f}"
)
if loss_f > 3.28:
    raise SystemExit(f"target miss: val_loss {loss_f:.4f} > 3.28")
PY
REMOTE
