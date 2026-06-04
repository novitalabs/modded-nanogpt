#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD:-modded-nanogpt-repro}"
TIMEOUT="${VARIANT_TIMEOUT:-45m}"
VARIANT_ID="${VARIANT_ID:?set VARIANT_ID}"
ABLATION="${ABLATION:?set ABLATION}"
TARGET_LOSS="${TARGET_LOSS:-3.28}"
RESULTS_DIR="${RESULTS_DIR:-experiments/results}"

kubectl exec -i "${POD}" -- bash -s -- "${TIMEOUT}" "${VARIANT_ID}" "${ABLATION}" "${TARGET_LOSS}" "${RESULTS_DIR}" <<'REMOTE'
set -euo pipefail
timeout_value="$1"
variant_id="$2"
ablation="$3"
target_loss="$4"
results_dir="$5"
cd /workspace/modded-nanogpt

active_train="$(ps -eo pid,comm,args | awk '/[t]orchrun .*train_gpt|[p]ython .*train_gpt|[p]ython .*\\.arthur_top10_/ {print}')"
if [[ -n "${active_train}" ]]; then
  echo "existing training process detected:"
  echo "${active_train}"
  exit 3
fi

variant_script=".arthur_top10_${variant_id}_$(date +%Y%m%d_%H%M%S).py"
cleanup() {
  rm -f "${variant_script}"
}
trap cleanup EXIT

python - "${variant_script}" "${ablation}" "${variant_id}" <<'PY'
import json
import sys
from pathlib import Path

target = Path(sys.argv[1])
ablation = sys.argv[2]
variant_id = sys.argv[3]
code = Path("train_gpt.py").read_text()

def replace_once(old: str, new: str) -> None:
    global code
    if old not in code:
        raise SystemExit(f"replacement source not found for {ablation}: {old!r}")
    code = code.replace(old, new, 1)

if ablation == "xsa_off":
    replace_once(
        "xsa_alphas = [xsa_alpha_per_layer[j] if j in {1, 3, 4, 7, 8, 10} else None for j in range(self.num_layers)]",
        "xsa_alphas = [None for _ in range(self.num_layers)]",
    )
elif ablation == "smear_off":
    replace_once(
        "smear_gate_out = smear_lambda * torch.sigmoid(self.smear_gate(x[1:, :self.smear_gate.weight.size(-1)]))",
        "smear_gate_out = torch.zeros_like(x[1:, :1])",
    )
elif ablation == "partial_key_offset_off":
    replace_once(
        "key_offset = [b==ws_long for b in bm_sizes] # apply partial key offset to long windows",
        "key_offset = [False for _ in bm_sizes] # Arthur ablation: disable partial key offset",
    )
elif ablation == "mtp_off":
    replace_once(
        "mtp_weights_start=[1.0, 0.5, 0.25], mtp_weights_end=[1.0, 0.5, 0.0]),",
        "mtp_weights_start=[1.0], mtp_weights_end=[1.0]),",
    )
    replace_once(
        "mtp_weights_start=[1.0, 0.5], mtp_weights_end=[1.0, 0.0]),",
        "mtp_weights_start=[1.0], mtp_weights_end=[1.0]),",
    )
elif ablation == "bigram_off":
    replace_once(
        "x0_bigram = self.bigram_embed(bigram_input_seq)[None]",
        "x0_bigram = self.bigram_embed(bigram_input_seq)[None] * 0",
    )
elif ablation == "value_embeds_off":
    replace_once(
        "ve = self.value_embeds.view(5, self.vocab_size, -1)[:, input_seq]",
        "ve = torch.zeros((5, input_seq.numel(), self.embed.weight.shape[1]), device=input_seq.device, dtype=self.embed.weight.dtype)",
    )
else:
    raise SystemExit(f"unknown ablation: {ablation}")

replace_once("val_loss_every: int = 250", "val_loss_every: int = 0")
replace_once('run_id: str = f"{uuid.uuid4()}"', f'run_id: str = "{variant_id}"')

banner = [
    "# Arthur README top10 ablation variant",
    f"# variant_id={variant_id}",
    f"# ablation={ablation}",
    "",
]
target.write_text("\n".join(banner) + code)
print(f"variant_script={target}")
PY

started_at="$(date -Iseconds)"
echo "starting readme_top10 variant=${variant_id} ablation=${ablation} pod=$(hostname) at ${started_at}"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

set +e
timeout "${timeout_value}" torchrun --standalone --nproc_per_node=8 "${variant_script}"
rc=$?
set -e

latest_log="logs/${variant_id}.txt"
if [[ ! -f "${latest_log}" ]]; then
  latest_log="$(find logs -maxdepth 1 -type f -name '*.txt' -newermt "${started_at}" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)"
fi
if [[ -z "${latest_log}" || ! -f "${latest_log}" ]]; then
  echo "no training log found after ablation run"
  exit 4
fi

echo "latest_log=${latest_log}"
tail -180 "${latest_log}"

mkdir -p "${results_dir}"
python experiments/collect_results.py

python - "${latest_log}" "${variant_id}" "${ablation}" "${target_loss}" "${results_dir}" "${rc}" <<'PY'
import csv
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
variant_id = sys.argv[2]
ablation = sys.argv[3]
target_loss = float(sys.argv[4])
results_dir = Path(sys.argv[5])
run_rc = int(sys.argv[6])
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
target_met = loss_f <= target_loss
row = {
    "variant_id": variant_id,
    "ablation": ablation,
    "log": str(path),
    "step": step,
    "total_steps": total,
    "val_loss": f"{loss_f:.6f}",
    "train_time_min": f"{train_min:.6f}",
    "step_avg_ms": f"{float(step_avg):.6f}",
    "target_loss": f"{target_loss:.6f}",
    "target_met": str(target_met).lower(),
    "run_exit_code": str(run_rc),
}
csv_path = results_dir / "readme_top10_ablation_results.csv"
write_header = not csv_path.exists()
with csv_path.open("a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(row))
    if write_header:
        writer.writeheader()
    writer.writerow(row)

json_path = results_dir / f"readme_top10_{variant_id}.json"
json_path.write_text(json.dumps(row, indent=2) + "\n")
print(
    f"final_result variant={variant_id} ablation={ablation} log={path} "
    f"step={step}/{total} val_loss={loss_f:.4f} train_time_min={train_min:.4f} "
    f"target_met={target_met}"
)
if run_rc != 0:
    raise SystemExit(f"training command exited {run_rc}")
PY
REMOTE
