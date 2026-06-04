#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD:-modded-nanogpt-repro}"
TIMEOUT="${VARIANT_TIMEOUT:-45m}"
VARIANT_ID="${VARIANT_ID:?set VARIANT_ID}"
ABLATION="${ABLATION:?set ABLATION}"
TARGET_LOSS="${TARGET_LOSS:-3.28}"
RESULTS_DIR="${RESULTS_DIR:-experiments/results}"

if [[ "${RUN_README_ABLATION_DIRECT:-0}" == "1" ]] || ! command -v kubectl >/dev/null 2>&1; then
  RUNNER=(bash -s -- "${TIMEOUT}" "${VARIANT_ID}" "${ABLATION}" "${TARGET_LOSS}" "${RESULTS_DIR}" "$(pwd -P)")
else
  RUNNER=(kubectl exec -i "${POD}" -- bash -s -- "${TIMEOUT}" "${VARIANT_ID}" "${ABLATION}" "${TARGET_LOSS}" "${RESULTS_DIR}" "/workspace/modded-nanogpt")
fi

"${RUNNER[@]}" <<'REMOTE'
set -euo pipefail
timeout_value="$1"
variant_id="$2"
ablation="$3"
target_loss="$4"
results_dir="$5"
workdir="$6"
cd "${workdir}"

python_bin="${PYTHON_BIN:-}"
if [[ -z "${python_bin}" ]]; then
  if command -v python >/dev/null 2>&1; then
    python_bin="python"
  elif command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  else
    echo "python/python3 not found"
    exit 127
  fi
fi

active_train="$(ps -eo pid,comm,args | awk '/[t]orchrun .*train_gpt|[p]ython[0-9.]* .*train_gpt|[p]ython[0-9.]* .*\\.arthur_top10_/ {print}')"
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

"${python_bin}" - "${variant_script}" "${ablation}" "${variant_id}" <<'VARIANT_PY'
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
elif ablation == "long_window_off":
    replace_once(
        "bm_sizes = [ws_short, ws_short, ws_short, ws_long, ws_short, ws_short, None, ws_short, ws_short, ws_short, ws_long]",
        "bm_sizes = [ws_short, ws_short, ws_short, ws_short, ws_short, ws_short, None, ws_short, ws_short, ws_short, ws_short]",
    )
elif ablation == "long_window_yarn_off":
    replace_once(
        "bm_sizes = [ws_short, ws_short, ws_short, ws_long, ws_short, ws_short, None, ws_short, ws_short, ws_short, ws_long]",
        "bm_sizes = [ws_short, ws_short, ws_short, ws_short, ws_short, ws_short, None, ws_short, ws_short, ws_short, ws_short]",
    )
    replace_once(
        """if new_ws_long != self.ws_long:
            self.model.yarn.apply(self.ws_long * self.block_size, new_ws_long * self.block_size)
            self.model.yarn_paired_head.apply(self.ws_long * self.block_size, new_ws_long * self.block_size)""",
        """if False and new_ws_long != self.ws_long:
            self.model.yarn.apply(self.ws_long * self.block_size, new_ws_long * self.block_size)
            self.model.yarn_paired_head.apply(self.ws_long * self.block_size, new_ws_long * self.block_size)""",
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
elif ablation == "fp8_lm_head_off":
    replace_once(
        'use_fp8 = not os.environ.get("DISABLE_FP8", False)',
        "use_fp8 = False",
    )
elif ablation == "fp8_lm_head_dense_train_off":
    replace_once(
        'use_fp8 = not os.environ.get("DISABLE_FP8", False)',
        "use_fp8 = False",
    )
    replace_once(
        """        if self.training:
            loss_per_token = FusedSoftcappedCrossEntropy.apply(x.view(-1, x.size(-1)), target_seq, mtp_weights, self.lm_head.weight, self.lm_head.x_s, self.lm_head.w_s, self.lm_head.grad_s, grad_scale)
        else:
            logits = self.lm_head(x)
            logits = 23 * torch.sigmoid((logits + 5) / 7.5)
            logits_for_loss = logits.float()
            loss_per_token = F.cross_entropy(logits_for_loss.view(-1, logits_for_loss.size(-1)), target_seq, reduction="none")""",
        """        logits = self.lm_head(x)
        logits = 23 * torch.sigmoid((logits + 5) / 7.5)
        logits_for_loss = logits.float()
        loss_per_token = torch.zeros_like(target_seq, dtype=logits_for_loss.dtype)
        for mtp_offset, mtp_weight in enumerate(mtp_weights):
            if mtp_offset == 0:
                loss_per_token += mtp_weight * F.cross_entropy(logits_for_loss.view(-1, logits_for_loss.size(-1)), target_seq, reduction="none")
            elif target_seq.numel() > mtp_offset:
                loss_per_token[:-mtp_offset] += mtp_weight * F.cross_entropy(logits_for_loss[:-mtp_offset].reshape(-1, logits_for_loss.size(-1)), target_seq[mtp_offset:], reduction="none")""",
    )
elif ablation == "batch_schedule_constant_final":
    replace_once(
        "TrainingStage(duration=1/3, train_max_seq_len=896, batch_size=8 * 2048 * 8, window_sizes=(1, 3), lr_mul=1.0,",
        "TrainingStage(duration=1/3, train_max_seq_len=896, batch_size=24 * 2048 * 8, window_sizes=(1, 3), lr_mul=1.0,",
    )
    replace_once(
        "TrainingStage(duration=1/3, train_max_seq_len=2048, batch_size=16 * 2048 * 8, window_sizes=(3, 7), lr_mul=1.52,",
        "TrainingStage(duration=1/3, train_max_seq_len=2048, batch_size=24 * 2048 * 8, window_sizes=(3, 7), lr_mul=1.52,",
    )
    replace_once(
        "TRAIN_MAX_NUM_DOCS = {16384: 64, 32768: 96, 49152: 128}",
        "TRAIN_MAX_NUM_DOCS = {16384: 64, 32768: 96, 49152: 256}",
    )
elif ablation == "batch_schedule_constant_mean":
    replace_once(
        "TrainingStage(duration=1/3, train_max_seq_len=896, batch_size=8 * 2048 * 8, window_sizes=(1, 3), lr_mul=1.0,",
        "TrainingStage(duration=1/3, train_max_seq_len=896, batch_size=16 * 2048 * 8, window_sizes=(1, 3), lr_mul=1.0,",
    )
    replace_once(
        "TrainingStage(duration=1/3, train_max_seq_len=2048, batch_size=24 * 2048 * 8, window_sizes=(5, 11), lr_mul=1.73,",
        "TrainingStage(duration=1/3, train_max_seq_len=2048, batch_size=16 * 2048 * 8, window_sizes=(5, 11), lr_mul=1.73,",
    )
elif ablation == "zero_mlp_proj_init_off":
    replace_once(
        "self.mlp_bank[:, 1, :, :].zero_()  # c_proj - zero init suggested by @Grad62304977",
        "self.mlp_bank[:, 1, :, :].uniform_(-bound, bound)  # Arthur ablation: disable c_proj zero init",
    )
elif ablation == "cautious_wd_off":
    replace_once(
        "mask = (update * p_slice) > 0",
        "mask = torch.ones_like(update, dtype=torch.bool)  # Arthur ablation: ordinary decoupled WD",
    )
    replace_once(
        "mask = (grad * p_precise) >= 0",
        "mask = torch.ones_like(p_precise, dtype=torch.bool)  # Arthur ablation: ordinary decoupled WD",
    )
elif ablation == "residual_decay_off":
    replace_once(
        "self.resid_lambdas = nn.Parameter(torch.full((num_layers, 2), 1.1**0.5))",
        "self.resid_lambdas = nn.Parameter(torch.ones(num_layers, 2))",
    )
    replace_once(
        "bs_init[0, 8]  = 1.1**0.5 / self._mudd_scale  # resid_attn[10]",
        "bs_init[0, 8]  = 1.0 / self._mudd_scale  # Arthur ablation: no residual scaling init",
    )
    replace_once(
        "bs_init[0, 12] = 1.1**0.5 / self._mudd_scale  # resid_mlp[10]",
        "bs_init[0, 12] = 1.0 / self._mudd_scale  # Arthur ablation: no residual scaling init",
    )
elif ablation == "embedding_skip_off":
    replace_once(
        "x0_inject = (x0 * x0_lambdas[0],) + tuple(x0 * x0_lambdas[i] + x0_bigram * bigram_lambdas[i] for i in range(1, self.num_layers))",
        "x0_inject = (torch.zeros_like(x0),) + tuple(x0_bigram * bigram_lambdas[i] for i in range(1, self.num_layers))",
    )
elif ablation == "block3_skip_off":
    replace_once(
        "x = x + skip_gate_out * cache[3]",
        "x = x  # Arthur ablation: disable block-3-to-layer-6 skip",
    )
elif ablation == "qk_norm_off":
    replace_once(
        "q, k = norm(q), norm(k) # QK norm @Grad62304977",
        "q, k = q, k  # Arthur ablation: disable QK norm",
    )
elif ablation == "polar_express_off":
    replace_once(
        """v_chunk = polar_express(
            grad_chunk, p_state["momentum_buffer"], self._momentum_t,
            split_baddbmm=is_large_matrix,
        )""",
        """momentum = self._momentum_t.to(grad_chunk.dtype)
        p_state["momentum_buffer"].lerp_(grad_chunk, 1 - momentum)
        v_chunk = grad_chunk.lerp(p_state["momentum_buffer"], momentum)""",
    )
elif ablation == "eos_alignment_off":
    train_loader_call = "distributed_data_generator(args.train_files, TRAINING_STAGES[0].batch_size, TRAINING_STAGES[0].train_max_seq_len, grad_accum_steps=grad_accum_steps)"
    replace_once(
        train_loader_call,
        "distributed_data_generator(args.train_files, TRAINING_STAGES[0].batch_size, TRAINING_STAGES[0].train_max_seq_len, grad_accum_steps=grad_accum_steps, align_to_bos=False)",
    )
    replace_once(
        train_loader_call,
        "distributed_data_generator(args.train_files, TRAINING_STAGES[0].batch_size, TRAINING_STAGES[0].train_max_seq_len, grad_accum_steps=grad_accum_steps, align_to_bos=False)",
    )
elif ablation == "max_doc_count_off":
    replace_once(
        "TRAIN_MAX_NUM_DOCS = {16384: 64, 32768: 96, 49152: 128}",
        "TRAIN_MAX_NUM_DOCS = {}  # Arthur ablation: use old heuristic max document count",
    )
elif ablation == "paired_head_off":
    replace_once(
        "self.paired_head_layers = [0, 2, 5, 9]",
        "self.paired_head_layers = []  # Arthur ablation: disable paired-head attention layers",
    )
elif ablation == "mudd_off":
    replace_once(
        "if i == self.num_layers - 1:",
        "if False and i == self.num_layers - 1:  # Arthur ablation: use non-MUDD final-layer path",
    )
    replace_once(
        "mu = self.forward_mudd(x, id=1, num_coef=5)",
        "mu = torch.zeros((x.size(0), x.size(1), 5), device=x.device, dtype=x.dtype)  # Arthur ablation: disable post-loop MUDD coefficients",
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
VARIANT_PY

if ! "${python_bin}" - <<'PY' >/dev/null 2>&1
import torch, triton
import kernels
PY
then
  echo "missing kernels package; attempting pip install kernels"
  "${python_bin}" -m pip install kernels
  "${python_bin}" - <<'PY'
import torch, triton
import kernels
print("python dependency preflight passed")
PY
fi

started_at="$(date -Iseconds)"
echo "starting readme_top10 variant=${variant_id} ablation=${ablation} pod=$(hostname) at ${started_at}"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

if command -v torchrun >/dev/null 2>&1; then
  launcher=(torchrun)
else
  launcher=("${python_bin}" -m torch.distributed.run)
fi

set +e
timeout "${timeout_value}" "${launcher[@]}" --standalone --nproc_per_node=8 "${variant_script}" </dev/null
rc=$?
set -e

latest_log="logs/${variant_id}.txt"
if [[ ! -f "${latest_log}" && -d logs ]]; then
  latest_log="$(find logs -maxdepth 1 -type f -name '*.txt' -newermt "${started_at}" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"
fi
if [[ -z "${latest_log}" || ! -f "${latest_log}" ]]; then
  echo "no training log found after ablation run"
  exit 4
fi

echo "latest_log=${latest_log}"
tail -180 "${latest_log}"

mkdir -p "${results_dir}"
"${python_bin}" experiments/collect_results.py

"${python_bin}" - "${latest_log}" "${variant_id}" "${ablation}" "${target_loss}" "${results_dir}" "${rc}" <<'RESULT_PY'
import csv
import json
import math
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
    r"step:(\d+)/(\d+)\s+val_loss:([0-9.]+|nan|inf|-inf)\s+train_time:([0-9.]+)ms\s+step_avg:([0-9.]+)ms",
    text,
    flags=re.IGNORECASE,
)
if not matches:
    raise SystemExit(f"no validation result found in {path}")

step, total, loss, train_ms, step_avg = matches[-1]
loss_f = float(loss)
train_min = float(train_ms) / 60000.0
target_met = math.isfinite(loss_f) and loss_f <= target_loss
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
RESULT_PY
REMOTE
