#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
RESULTS = ROOT / "experiments" / "results"

TECHNIQUES = [
    "Modernized architecture: Rotary embeddings, QK-Norm, and ReLU2",
    "Muon optimizer",
    "FP8 lm_head, asymmetric rescale, and softcap logits",
    "Zero initialization of projections",
    "Embedding/block skip connections",
    "Value embeddings",
    "Flash Attention 3, long-short sliding windows, window warmup, YaRN",
    "EoS-aligned batches and max document length",
    "Embedding/lm_head gradient accumulation",
    "Single activation input for last attention layers",
    "Polar Express in Muon",
    "Smear one-token lookback",
    "Sparse attention gate",
    "NorMuon",
    "Cautious Weight Decay",
    "Residual stream exponential decay",
    "Batch size schedule",
    "Max seq length schedule",
    "Partial Key Offset",
    "Multi-token prediction",
    "Untie embed and lm_head at 2/3 training",
    "Value embedding and skip gates",
    "Paired head attention",
    "Bigram hash embedding",
    "MUDD skip connections",
    "Learnable XSA",
]

KEYWORDS = {
    "Modernized architecture: Rotary embeddings, QK-Norm, and ReLU2": ["rotary", "qk-norm", "relu"],
    "Muon optimizer": ["muon"],
    "FP8 lm_head, asymmetric rescale, and softcap logits": ["fp8", "softcap", "rescale"],
    "Zero initialization of projections": ["zero-init", "zero initialization"],
    "Embedding/block skip connections": ["skip connection", "shortcuts", "u-net pattern skip"],
    "Value embeddings": ["value embed", "value embeddings"],
    "Flash Attention 3, long-short sliding windows, window warmup, YaRN": ["flash attention 3", "fa3", "long-short", "window warmup", "yarn"],
    "EoS-aligned batches and max document length": ["align training batch starts", "max_doc_len", "max document"],
    "Embedding/lm_head gradient accumulation": ["accumulate gradients", "custombatching"],
    "Single activation input for last attention layers": ["single saved activation", "partitioned hyperconnections"],
    "Polar Express in Muon": ["polar express"],
    "Smear one-token lookback": ["smear"],
    "Sparse attention gate": ["sparse attention gate"],
    "NorMuon": ["normuon"],
    "Cautious Weight Decay": ["cautious weight decay", "cautiouswd"],
    "Residual stream exponential decay": ["exponential decay", "residual"],
    "Batch size schedule": ["batch size schedule", "reduced batch size"],
    "Max seq length schedule": ["max_seq_len schedule", "shortwindow", "short window"],
    "Partial Key Offset": ["partial key offset"],
    "Multi-token prediction": ["multi-token prediction", "multi token prediction"],
    "Untie embed and lm_head at 2/3 training": ["untie embed", "retie embed"],
    "Value embedding and skip gates": ["gates on value", "ve_gates", "skip connection gating"],
    "Paired head attention": ["paired head attention"],
    "Bigram hash embedding": ["bigram hash"],
    "MUDD skip connections": ["mudd"],
    "Learnable XSA": ["learnable xsa", "xsa"],
}


def read_records() -> list[dict[str, str]]:
    path = RESULTS / "readme_records.csv"
    if not path.exists():
        raise SystemExit("experiments/results/readme_records.csv missing; run experiments/collect_results.py first")
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def pct_delta(prev: float, cur: float) -> float:
    return (prev - cur) / prev * 100.0


def infer_matches(text: str) -> list[str]:
    low = text.lower()
    matches = []
    for technique, needles in KEYWORDS.items():
        if any(n.lower() in low for n in needles):
            matches.append(technique)
    return matches


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    records = [r for r in read_records() if r.get("track") == "track_1_short"]
    records = [r for r in records if r.get("record_time_min")]
    records.sort(key=lambda r: int(r["row_index"]))

    rows = []
    previous = None
    for record in records:
        current = float(record["record_time_min"])
        if previous is None:
            previous = current
            continue
        desc = record.get("description_text") or record.get("description") or ""
        matches = infer_matches(desc)
        if not matches:
            previous = current
            continue
        delta_min = previous - current
        share = delta_min / len(matches)
        for technique in matches:
            rows.append({
                "technique": technique,
                "record_number": record["record_number"],
                "date": record["date"],
                "description": desc,
                "previous_time_min": f"{previous:.6f}",
                "record_time_min": f"{current:.6f}",
                "delta_min": f"{share:.6f}",
                "delta_pct": f"{pct_delta(previous, current) / len(matches):.6f}",
                "attribution": "historical_description_keyword_split",
            })
        previous = current

    totals = {tech: {"technique": tech, "historical_delta_min": 0.0, "historical_delta_pct": 0.0, "mentions": 0} for tech in TECHNIQUES}
    for row in rows:
        total = totals[row["technique"]]
        total["historical_delta_min"] += float(row["delta_min"])
        total["historical_delta_pct"] += float(row["delta_pct"])
        total["mentions"] += 1

    ranked = sorted(totals.values(), key=lambda r: (r["historical_delta_min"], r["historical_delta_pct"]), reverse=True)
    for idx, row in enumerate(ranked, 1):
        row["historical_rank"] = idx
        row["ablation_status"] = "pending"

    detail_path = RESULTS / "readme_top10_historical_details.csv"
    with detail_path.open("w", newline="") as f:
        fieldnames = ["technique", "record_number", "date", "description", "previous_time_min", "record_time_min", "delta_min", "delta_pct", "attribution"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ranking_path = RESULTS / "readme_top10_ranking.csv"
    with ranking_path.open("w", newline="") as f:
        fieldnames = ["historical_rank", "technique", "historical_delta_min", "historical_delta_pct", "mentions", "ablation_status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in ranked:
            writer.writerow({
                "historical_rank": row["historical_rank"],
                "technique": row["technique"],
                "historical_delta_min": f"{row['historical_delta_min']:.6f}",
                "historical_delta_pct": f"{row['historical_delta_pct']:.6f}",
                "mentions": row["mentions"],
                "ablation_status": row["ablation_status"],
            })

    summary = {
        "objective": "rank top10 README optimization methods by historical speedup prior and current-code ablation evidence",
        "method": "keyword attribution over README record deltas; multi-technique records split credit equally",
        "ranking_csv": str(ranking_path.relative_to(ROOT)),
        "details_csv": str(detail_path.relative_to(ROOT)),
        "top10": ranked[:10],
    }
    summary_path = RESULTS / "readme_top10_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    md_path = RESULTS / "readme_top10_plan.md"
    lines = [
        "# README Top10 Optimization Plan",
        "",
        "Goal: identify the top 10 most effective optimization methods listed in README.",
        "",
        "Method:",
        "- Use README record-history deltas as the historical prior.",
        "- Split credit across multiple named techniques in the same record.",
        "- Validate current-code effects with safe reversible ablations first.",
        "- Treat historical ranking as prior evidence, not causal proof.",
        "",
        "Current historical top 10:",
        "",
        "| rank | technique | delta min | delta pct | mentions |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in ranked[:10]:
        lines.append(
            f"| {row['historical_rank']} | {row['technique']} | "
            f"{row['historical_delta_min']:.3f} | {row['historical_delta_pct']:.2f}% | {row['mentions']} |"
        )
    lines.extend([
        "",
        "First ablation batch:",
        "- Learnable XSA off",
        "- Smear off",
        "- Partial Key Offset off",
        "- Multi-token prediction off",
        "- Bigram hash embedding off",
        "- Value embeddings off",
        "",
        "Deferred ablations need more careful code surgery: MUDD, NorMuon/Polar Express, FA3/window schedule, Cautious Weight Decay, paired heads, and batch/sequence schedules.",
    ])
    md_path.write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
