#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD:-modded-nanogpt-repro}"

kubectl exec -i "${POD}" -- bash -s <<'REMOTE'
set -euo pipefail
cd /workspace/modded-nanogpt

python experiments/collect_results.py
python - <<'PY'
import csv
import json
from pathlib import Path

root = Path("experiments/results")
print("summary=" + json.dumps(json.loads((root / "summary.json").read_text()), sort_keys=True))

local = root / "local_reruns.csv"
if local.exists():
    rows = list(csv.DictReader(local.open()))
    print("local_reruns:")
    for row in rows:
        print(
            f"{row['label']} track={row['track']} runs={row['runs']} "
            f"target_met={row['target_met_runs']} "
            f"best_target_min={row['target_train_time_min_best']} "
            f"best_val={row['target_val_loss_best']}"
        )
PY
REMOTE
