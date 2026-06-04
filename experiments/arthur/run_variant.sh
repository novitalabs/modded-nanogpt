#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD:-modded-nanogpt-repro}"
TIMEOUT="${VARIANT_TIMEOUT:-45m}"
VARIANT_ID="${VARIANT_ID:?set VARIANT_ID}"
REPLACEMENTS_JSON="${REPLACEMENTS_JSON:?set REPLACEMENTS_JSON to a JSON object of exact source replacements}"
WARMUP_CLAMP="${WARMUP_CLAMP:-0}"

kubectl exec -i "${POD}" -- bash -s -- "${TIMEOUT}" "${VARIANT_ID}" "${REPLACEMENTS_JSON}" "${WARMUP_CLAMP}" <<'REMOTE'
set -euo pipefail
timeout_value="$1"
variant_id="$2"
replacements_json="$3"
warmup_clamp="$4"
cd /workspace/modded-nanogpt

active_train="$(ps -eo pid,comm,args | awk '/[t]orchrun .*train_gpt|[p]ython .*train_gpt|[p]ython .*\\.arthur_variant_/ {print}')"
if [[ -n "${active_train}" ]]; then
  echo "existing training process detected:"
  echo "${active_train}"
  exit 3
fi

variant_script=".arthur_variant_${variant_id}_$(date +%Y%m%d_%H%M%S).py"
cleanup() {
  rm -f "${variant_script}"
}
trap cleanup EXIT

python - "${variant_script}" "${replacements_json}" "${warmup_clamp}" <<'PY'
import json
import sys
from pathlib import Path

target = Path(sys.argv[1])
replacements = json.loads(sys.argv[2])
warmup_clamp = sys.argv[3] == "1"
code = Path("train_gpt.py").read_text()
for old, new in replacements.items():
    if old not in code:
        raise SystemExit(f"replacement source not found: {old!r}")
    code = code.replace(old, new, 1)

if warmup_clamp:
    old = "warmup_steps = sorted({0, 1} | {s + offset for s in transition_steps for offset in [-2, -1, 0, 1] if s + offset >= 2})"
    new = "warmup_steps = sorted({step for step in ({0, 1} | {s + offset for s in transition_steps for offset in [-2, -1, 0, 1] if s + offset >= 2}) if step <= training_schedule.total_steps})"
    if old in code:
        code = code.replace(old, new, 1)
    elif "<= training_schedule.total_steps" not in code:
        raise SystemExit("warmup clamp source not found")

banner = [
    f"# Arthur variant generated from train_gpt.py",
    f"# replacements={json.dumps(replacements, sort_keys=True)}",
    f"# warmup_clamp={warmup_clamp}",
    "",
]
target.write_text("\n".join(banner) + code)
print(f"variant_script={target}")
PY

echo "starting variant=${variant_id} at $(date -Iseconds)"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

timeout "${timeout_value}" torchrun --standalone --nproc_per_node=8 "${variant_script}"

latest_log="$(find logs -maxdepth 1 -type f -name '*.txt' -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)"
if [[ -z "${latest_log}" ]]; then
  echo "no training log found after variant run"
  exit 4
fi

echo "latest_log=${latest_log}"
tail -180 "${latest_log}"
python experiments/collect_results.py

python - "${latest_log}" "${variant_id}" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
variant_id = sys.argv[2]
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
    f"final_result variant={variant_id} log={path} step={step}/{total} "
    f"val_loss={loss_f:.4f} train_time_min={train_min:.4f} step_avg_ms={float(step_avg):.2f}"
)
if loss_f > 3.28:
    raise SystemExit(f"target miss: val_loss {loss_f:.4f} > 3.28")
PY
REMOTE
