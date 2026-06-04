#!/usr/bin/env python3
"""Collect README records, stored logs, and local rerun logs.

The repo keeps most historical speedrun entries as logs rather than runnable
source snapshots. This script makes that explicit by separating README claims,
parsed log results, code availability, and local reruns.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results"
README = ROOT / "README.md"

LOG_EXTENSIONS = {".log", ".txt"}
TARGET_LOSS_BY_TRACK = {
    "track_1_short": 3.28,
    "track_2_medium": 2.92,
}
LOCAL_RERUN_RECORD_DIRS = {
    "2024-10-10_Muon": "records/track_1_short/2024-10-10_Muon",
    "2024-10-14_ModernArch": "records/track_1_short/2024-10-14_ModernArch",
    "2024-12-04_ValueEmbed": "records/track_1_short/2024-12-04_ValueEmbed",
    "2025-11-12_BlockMaskRedundantOp": "records/track_2_medium/2025-11-12_BlockMaskRedundantOp",
}
TRACKS = {
    "track_1_short": {
        "title": "track_1_short",
        "start": "## World record history",
        "end": "## Rules",
        "records_dir": ROOT / "records" / "track_1_short",
    },
    "track_2_medium": {
        "title": "track_2_medium",
        "start": "## Speedrun track 2: GPT-2 Medium",
        "end": "### Q: What is the point of NanoGPT speedrunning?",
        "records_dir": ROOT / "records" / "track_2_medium",
    },
}

VAL_RE = re.compile(
    r"step:(?P<step>\d+)/(?P<total>\d+)\s+"
    r"val_loss:(?P<val_loss>[0-9]+(?:\.[0-9]+)?)\s+"
    r"train_time:(?P<train_time_ms>[0-9]+(?:\.[0-9]+)?)ms\s+"
    r"step_avg:(?P<step_avg_ms>[0-9]+(?:\.[0-9]+)?)ms"
)
PEAK_RE = re.compile(
    r"peak memory allocated:\s+(?P<allocated>\d+)\s+MiB\s+reserved:\s+(?P<reserved>\d+)\s+MiB"
)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass
class ReadmeRecord:
    track: str
    row_index: int
    record_number: str
    record_time_text: str
    record_time_min: float | None
    description: str
    description_text: str
    date: str
    log_field: str
    contributors: str
    log_paths: str
    code_paths: str
    availability: str = ""
    parsed_log_path: str = ""
    parsed_log_val_loss: float | None = None
    parsed_log_train_time_min: float | None = None
    parsed_log_train_time_delta_min: float | None = None
    parsed_log_train_time_delta_pct: float | None = None


@dataclass
class LogResult:
    source: str
    track: str
    path: str
    final_step: int
    total_steps: int
    val_loss: float
    train_time_ms: float
    train_time_min: float
    step_avg_ms: float
    peak_allocated_mib: int | None
    peak_reserved_mib: int | None
    completed: bool
    target_met: bool


@dataclass
class RerunSummary:
    label: str
    track: str
    runs: int
    target_met_runs: int
    all_train_time_min_mean: float | None
    all_train_time_min_best: float | None
    all_val_loss_mean: float | None
    all_val_loss_best: float | None
    target_train_time_min_mean: float | None
    target_train_time_min_best: float | None
    target_val_loss_mean: float | None
    target_val_loss_best: float | None
    paths: str


@dataclass
class FailedLocalRun:
    label: str
    track: str
    path: str
    error_type: str
    reason: str


def clean_markdown(text: str) -> str:
    text = LINK_RE.sub(lambda m: m.group(1), text)
    return re.sub(r"\s+", " ", text).strip()


def parse_time_min(text: str) -> float | None:
    cleaned = text.replace("*", "").strip().lower()
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(minute|minutes|min)\b", cleaned)
    if m:
        return float(m.group(1))
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(hour|hours|hr)\b", cleaned)
    if m:
        return float(m.group(1)) * 60.0
    return None


def section_lines(text: str, start_marker: str, end_marker: str) -> list[str]:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end].splitlines()


def split_table_line(line: str) -> list[str] | None:
    if "|" not in line:
        return None
    if line.lstrip().startswith("|"):
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
    else:
        parts = [p.strip() for p in line.split("|")]
    if len(parts) != 6:
        return None
    if parts[0] in {"#", "-"} or parts[0].startswith("-"):
        return None
    if not re.fullmatch(r"\d+", parts[0].strip()):
        return None
    return parts


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def extract_log_paths(log_field: str) -> list[Path]:
    paths: list[Path] = []
    for _, url in LINK_RE.findall(log_field):
        if url.startswith("http://") or url.startswith("https://") or url.startswith("#"):
            continue
        path = (ROOT / url).resolve()
        if path.exists():
            paths.append(path)
    return paths


def discover_code_paths(log_paths: list[Path]) -> list[Path]:
    code_paths: list[Path] = []
    seen: set[Path] = set()
    for path in log_paths:
        dirs: list[Path]
        if path.is_dir():
            dirs = [path]
        else:
            dirs = [path.parent]
        for directory in dirs:
            for pattern in ("train*.py", "*.py"):
                for candidate in sorted(directory.glob(pattern)):
                    if candidate.name.startswith("analyze_"):
                        continue
                    if candidate not in seen:
                        seen.add(candidate)
                        code_paths.append(candidate)
    return code_paths


def parse_readme_records() -> list[ReadmeRecord]:
    text = README.read_text(encoding="utf-8")
    records: list[ReadmeRecord] = []
    for track, cfg in TRACKS.items():
        row_index = 0
        for line in section_lines(text, cfg["start"], cfg["end"]):
            parts = split_table_line(line)
            if not parts:
                continue
            row_index += 1
            record_number, time_text, desc, date, log_field, contributors = parts
            log_paths = extract_log_paths(log_field)
            code_paths = discover_code_paths(log_paths)
            records.append(
                ReadmeRecord(
                    track=track,
                    row_index=row_index,
                    record_number=record_number,
                    record_time_text=time_text,
                    record_time_min=parse_time_min(time_text),
                    description=desc,
                    description_text=clean_markdown(desc),
                    date=date,
                    log_field=log_field,
                    contributors=contributors,
                    log_paths=";".join(repo_relative(p) for p in log_paths),
                    code_paths=";".join(repo_relative(p) for p in code_paths),
                )
            )
    return records


def infer_local_track(text: str, total_steps: int | None = None) -> str:
    if (
        "records/track_2_medium/" in text
        or "train_gpt_medium.py" in text
        or "num_iterations = 5960" in text
        or total_steps == 5960
    ):
        return "track_2_medium"
    return "track_1_short"


def parse_log_file(path: Path, source: str, track: str) -> LogResult | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    matches = list(VAL_RE.finditer(text))
    if not matches:
        return None
    last = matches[-1]
    train_time_ms = float(last.group("train_time_ms"))
    total_steps = int(last.group("total"))
    if source == "local_rerun" and track == "auto":
        track = infer_local_track(text, total_steps)
    peak = None
    peak_matches = list(PEAK_RE.finditer(text))
    if peak_matches:
        peak = peak_matches[-1]
    val_loss = float(last.group("val_loss"))
    target_loss = TARGET_LOSS_BY_TRACK.get(track, 3.28)
    final_step = int(last.group("step"))
    return LogResult(
        source=source,
        track=track,
        path=repo_relative(path),
        final_step=final_step,
        total_steps=total_steps,
        val_loss=val_loss,
        train_time_ms=train_time_ms,
        train_time_min=train_time_ms / 60000.0,
        step_avg_ms=float(last.group("step_avg_ms")),
        peak_allocated_mib=int(peak.group("allocated")) if peak else None,
        peak_reserved_mib=int(peak.group("reserved")) if peak else None,
        completed=final_step == total_steps,
        target_met=(final_step == total_steps and val_loss <= target_loss),
    )


def infer_failed_local_label(text: str) -> tuple[str, str]:
    track = infer_local_track(text)
    if (
        "2025-11-12_BlockMaskRedundantOp" in text
        or "train_gpt_medium.py" in text
        or (track == "track_2_medium" and "num_iterations = 5960" in text)
    ):
        return "2025-11-12_BlockMaskRedundantOp", track
    if "2024-10-10_Muon" in text:
        return "2024-10-10_Muon", track
    if "2024-10-14_ModernArch" in text:
        return "2024-10-14_ModernArch", track
    if "2024-12-04_ValueEmbed" in text:
        return "2024-12-04_ValueEmbed", track
    if "Learnable XSA" in text or "load_flash_attn_interface" in text:
        return "current_root_learnable_xsa", track
    return "unknown", track


def parse_failed_local_run(path: Path) -> FailedLocalRun | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    matches = list(VAL_RE.finditer(text))
    if matches:
        last = matches[-1]
        final_step = int(last.group("step"))
        total_steps = int(last.group("total"))
        if final_step >= total_steps:
            return None
        label, track = infer_failed_local_label(text)
        if label == "unknown":
            label = infer_rerun_label(
                LogResult(
                    source="local_rerun",
                    track=infer_local_track(text, total_steps),
                    path=repo_relative(path),
                    final_step=final_step,
                    total_steps=total_steps,
                    val_loss=float(last.group("val_loss")),
                    train_time_ms=float(last.group("train_time_ms")),
                    train_time_min=float(last.group("train_time_ms")) / 60000.0,
                    step_avg_ms=float(last.group("step_avg_ms")),
                    peak_allocated_mib=None,
                    peak_reserved_mib=None,
                    completed=False,
                    target_met=False,
                )
            )
            track = infer_local_track(text, total_steps)
        if "StopIteration" in text or "generator raised StopIteration" in text:
            error_type = "insufficient_data_shards"
            reason = "Training data shard iterator was exhausted before the requested number of steps"
        else:
            error_type = "partial_run"
            reason = f"Exited before completion after validation step {final_step}/{total_steps}"
        return FailedLocalRun(
            label=label,
            track=track,
            path=repo_relative(path),
            error_type=error_type,
            reason=reason,
        )
    has_runtime_step = re.search(r"^step:\d+/", text, flags=re.MULTILINE) is not None
    incomplete_logged_start = (
        "Running PyTorch" in text
        and "num_iterations = 5960" in text
        and not has_runtime_step
    )
    if "Traceback" not in text and "FAILED" not in text and "ChildFailedError" not in text and not incomplete_logged_start:
        return None
    label, track = infer_failed_local_label(text)
    if "Detected that you are using FX to symbolically trace a dynamo-optimized function" in text:
        error_type = "torch_dynamo_flex_attention"
        reason = "Torch 2.11 Dynamo/FlexAttention incompatibility during compiled autograd startup"
    elif "generator raised StopIteration" in text or "StopIteration" in text:
        error_type = "insufficient_data_shards"
        reason = "Training data shard iterator was exhausted before the requested number of steps"
    elif "_patched_trace_structured() missing" in text:
        error_type = "torch_trace_hook_signature"
        reason = "Torch 2.11 called trace_structured without metadata_fn on a cache hit"
    elif incomplete_logged_start and label == "2025-11-12_BlockMaskRedundantOp":
        error_type = "startup_failure"
        reason = "Exited before validation; kubectl stderr showed Torch 2.11 Dynamo/FlexAttention compiled-autograd incompatibility"
    elif "CUDA out of memory" in text:
        error_type = "cuda_oom"
        reason = "CUDA out of memory"
    else:
        error_type = "runtime_failure"
        reason = "Runtime failure before any validation result was emitted"
    return FailedLocalRun(
        label=label,
        track=track,
        path=repo_relative(path),
        error_type=error_type,
        reason=reason,
    )


def scan_logs() -> list[LogResult]:
    results: list[LogResult] = []
    for track, cfg in TRACKS.items():
        records_dir = cfg["records_dir"]
        if records_dir.exists():
            for path in sorted(records_dir.rglob("*")):
                if path.is_file() and path.suffix in LOG_EXTENSIONS:
                    parsed = parse_log_file(path, "records", track)
                    if parsed:
                        results.append(parsed)
    local_logs = ROOT / "logs"
    if local_logs.exists():
        for path in sorted(local_logs.glob("*")):
            if path.is_file() and path.suffix in LOG_EXTENSIONS:
                parsed = parse_log_file(path, "local_rerun", "auto")
                if parsed:
                    results.append(parsed)
    return results


def scan_failed_local_runs() -> list[FailedLocalRun]:
    results: list[FailedLocalRun] = []
    local_logs = ROOT / "logs"
    if not local_logs.exists():
        return results
    for path in sorted(local_logs.glob("*")):
        if path.is_file() and path.suffix in LOG_EXTENSIONS:
            parsed = parse_failed_local_run(path)
            if parsed:
                results.append(parsed)
    return results


def expand_reference_paths(record: ReadmeRecord) -> list[str]:
    paths: list[str] = []
    for item in record.log_paths.split(";"):
        if not item:
            continue
        path = ROOT / item
        if path.is_file():
            paths.append(repo_relative(path))
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix in LOG_EXTENSIONS:
                    paths.append(repo_relative(child))
    return paths


def attach_log_results(records: list[ReadmeRecord], logs: list[LogResult]) -> None:
    by_path = {log.path: log for log in logs}
    for record in records:
        candidates = [by_path[p] for p in expand_reference_paths(record) if p in by_path]
        valid = [log for log in candidates if log.target_met]
        if valid:
            best = min(valid, key=lambda log: log.train_time_min)
        elif candidates:
            best = min(candidates, key=lambda log: log.train_time_min)
        else:
            best = None

        has_code = bool(record.code_paths)
        if record.track == "track_1_short" and record.record_number == "82":
            root_train = ROOT / "train_gpt.py"
            if root_train.exists() and repo_relative(root_train) not in record.code_paths.split(";"):
                record.code_paths = (record.code_paths + ";" if record.code_paths else "") + repo_relative(root_train)
                has_code = True

        local_matches = [log for log in logs if record_matches_local_rerun(record, log)]

        if local_matches:
            record.availability = "rerun_completed"
        elif has_code:
            record.availability = "code_available"
        elif best is not None:
            record.availability = "log_available"
        else:
            record.availability = "readme_only"

        if best is not None:
            record.parsed_log_path = best.path
            record.parsed_log_val_loss = best.val_loss
            record.parsed_log_train_time_min = best.train_time_min
            if record.record_time_min is not None:
                delta = best.train_time_min - record.record_time_min
                record.parsed_log_train_time_delta_min = delta
            record.parsed_log_train_time_delta_pct = delta / record.record_time_min * 100.0


def record_matches_local_rerun(record: ReadmeRecord, log: LogResult) -> bool:
    if log.source != "local_rerun" or record.track != log.track or not log.completed:
        return False
    label = infer_rerun_label(log)
    if label == "current_root_learnable_xsa":
        return record.track == "track_1_short" and record.record_number == "82"
    if label == "2025-11-12_BlockMaskRedundantOp":
        return record.track == "track_2_medium" and record.record_number == "17"
    expected_dir = LOCAL_RERUN_RECORD_DIRS.get(label)
    if not expected_dir:
        return False
    record_paths = ";".join([record.log_paths, record.code_paths])
    return expected_dir in record_paths


def infer_rerun_label(log: LogResult) -> str:
    if log.source != "local_rerun":
        return "not_local"
    if log.total_steps in {1385, 1410, 1450, 1480}:
        return "current_root_learnable_xsa"
    if log.total_steps == 6000 and log.step_avg_ms > 300:
        return "2024-10-09_SOAP"
    if log.total_steps == 6200:
        return "2024-10-10_Muon"
    if log.total_steps == 5100:
        return "2024-10-14_ModernArch"
    if log.total_steps == 1530:
        return "2024-12-04_ValueEmbed"
    if log.total_steps == 5960:
        return "2025-11-12_BlockMaskRedundantOp"
    return f"unknown_total_steps_{log.total_steps}"


def summarize_local_reruns(logs: list[LogResult]) -> list[RerunSummary]:
    groups: dict[str, list[LogResult]] = {}
    for log in logs:
        if log.source != "local_rerun" or not log.completed:
            continue
        groups.setdefault(infer_rerun_label(log), []).append(log)

    summaries: list[RerunSummary] = []
    for label, items in sorted(groups.items()):
        all_times = [x.train_time_min for x in items]
        all_losses = [x.val_loss for x in items]
        valid_times = [x.train_time_min for x in items if x.target_met]
        valid_losses = [x.val_loss for x in items if x.target_met]
        summaries.append(
            RerunSummary(
                label=label,
                track=items[0].track,
                runs=len(items),
                target_met_runs=sum(1 for x in items if x.target_met),
                all_train_time_min_mean=mean(all_times) if all_times else None,
                all_train_time_min_best=min(all_times) if all_times else None,
                all_val_loss_mean=mean(all_losses) if all_losses else None,
                all_val_loss_best=min(all_losses) if all_losses else None,
                target_train_time_min_mean=mean(valid_times) if valid_times else None,
                target_train_time_min_best=min(valid_times) if valid_times else None,
                target_val_loss_mean=mean(valid_losses) if valid_losses else None,
                target_val_loss_best=min(valid_losses) if valid_losses else None,
                paths=";".join(x.path for x in items),
            )
        )
    return summaries


def find_readme_record_for_rerun(label: str, records: list[ReadmeRecord]) -> ReadmeRecord | None:
    if label == "current_root_learnable_xsa":
        return next((r for r in records if r.track == "track_1_short" and r.record_number == "82"), None)
    if label == "2025-11-12_BlockMaskRedundantOp":
        return next((r for r in records if r.track == "track_2_medium" and r.record_number == "17"), None)
    expected_dir = LOCAL_RERUN_RECORD_DIRS.get(label)
    if expected_dir is None:
        return None
    return next(
        (
            r
            for r in records
            if expected_dir in ";".join([r.log_paths, r.code_paths])
        ),
        None,
    )


def build_local_rerun_comparisons(
    records: list[ReadmeRecord], reruns: list[RerunSummary]
) -> list[dict[str, str | float | None]]:
    rows: list[dict[str, str | float | None]] = []
    for rerun in reruns:
        record = find_readme_record_for_rerun(rerun.label, records)
        if record is None:
            continue
        local_min = rerun.target_train_time_min_best
        delta_min = None
        delta_pct = None
        if local_min is not None and record.record_time_min is not None:
            delta_min = local_min - record.record_time_min
            delta_pct = delta_min / record.record_time_min * 100.0
        rows.append(
            {
                "label": rerun.label,
                "track": rerun.track,
                "record_number": record.record_number,
                "description": record.description_text,
                "readme_min": record.record_time_min,
                "local_target_best_min": local_min,
                "delta_min": delta_min,
                "delta_pct": delta_pct,
                "target_met_runs": rerun.target_met_runs,
                "runs": rerun.runs,
                "local_best_val_loss": rerun.target_val_loss_best,
                "paths": rerun.paths,
            }
        )
    return rows


def parse_top_techniques() -> list[dict[str, str]]:
    text = README.read_text(encoding="utf-8")
    start = text.index("This improvement in training speed has been brought about by the following techniques:")
    end = text.index("As well as many systems optimizations.", start)
    techniques = []
    for line in text[start:end].splitlines():
        if line.startswith("* "):
            techniques.append({"technique": clean_markdown(line[2:])})
    return techniques


def write_csv(path: Path, rows: list[object]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    dict_rows = [asdict(row) if hasattr(row, "__dataclass_fields__") else row for row in rows]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(dict_rows[0].keys()))
        writer.writeheader()
        writer.writerows(dict_rows)


def fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_report(
    records: list[ReadmeRecord],
    logs: list[LogResult],
    reruns: list[RerunSummary],
    failed_runs: list[FailedLocalRun],
    techniques: list[dict[str, str]],
) -> None:
    availability_counts: dict[str, int] = {}
    for record in records:
        availability_counts[record.availability] = availability_counts.get(record.availability, 0) + 1

    local_current = [
        log for log in logs if log.source == "local_rerun" and infer_rerun_label(log) == "current_root_learnable_xsa"
    ]
    official_latest = next((r for r in records if r.track == "track_1_short" and r.record_number == "82"), None)

    lines: list[str] = []
    lines.append("# Modded-NanoGPT Reproduction Report")
    lines.append("")
    lines.append("Generated by `experiments/collect_results.py`.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "- README records are treated as claims; stored logs are parsed independently; local reruns are parsed from `logs/`."
    )
    lines.append(
        "- Most historical entries in `records/` are log-only. Only entries with a `train*.py` snapshot, plus the root `train_gpt.py`, are marked code-available."
    )
    lines.append("- Official README timing is for 8xH100; local reruns here use the current K8s Pod on node `.72`.")
    lines.append("")
    lines.append("## Availability")
    lines.append("")
    lines.append(
        markdown_table(
            ["availability", "count"],
            [[key, str(availability_counts[key])] for key in sorted(availability_counts)],
        )
    )
    lines.append("")
    lines.append("## Current Record Rerun")
    lines.append("")
    if official_latest:
        lines.append(
            f"- README latest short-track record: #{official_latest.record_number} "
            f"`{official_latest.description_text}`, claimed {fmt(official_latest.record_time_min)} min."
        )
        if official_latest.parsed_log_train_time_min is not None:
            lines.append(
                f"- Parsed official/reference log: {fmt(official_latest.parsed_log_train_time_min)} min, "
                f"val_loss {fmt(official_latest.parsed_log_val_loss, 4)}."
            )
    if local_current:
        valid = [x for x in local_current if x.target_met]
        lines.append(
            f"- Local current-root reruns: {len(local_current)} total, {len(valid)} met target."
        )
        if valid:
            lines.append(
                f"- Local best: {min(x.train_time_min for x in valid):.3f} min, "
                f"mean: {mean(x.train_time_min for x in valid):.3f} min, "
                f"best val_loss: {min(x.val_loss for x in valid):.4f}."
            )
    lines.append("")
    lines.append("## Local Rerun Summary")
    lines.append("")
    rerun_comparisons = build_local_rerun_comparisons(records, reruns)
    lines.append(
        markdown_table(
            [
                "label",
                "runs",
                "target_met",
                "all_best_min",
                "all_mean_min",
                "all_best_val",
                "target_best_min",
                "target_mean_min",
                "target_best_val",
                "paths",
            ],
            [
                [
                    r.label,
                    str(r.runs),
                    str(r.target_met_runs),
                    fmt(r.all_train_time_min_best),
                    fmt(r.all_train_time_min_mean),
                    fmt(r.all_val_loss_best, 4),
                    fmt(r.target_train_time_min_best),
                    fmt(r.target_train_time_min_mean),
                    fmt(r.target_val_loss_best, 4),
                    r.paths,
                ]
                for r in reruns
            ],
        )
    )
    lines.append("")
    if rerun_comparisons:
        lines.append("## Local Rerun vs README")
        lines.append("")
        lines.append(
            markdown_table(
                [
                    "label",
                    "track",
                    "#",
                    "README min",
                    "local target best min",
                    "delta min",
                    "delta %",
                    "target_met/runs",
                    "local best val",
                    "description",
                    "paths",
                ],
                [
                    [
                        str(r["label"]),
                        str(r["track"]),
                        str(r["record_number"]),
                        fmt(r["readme_min"]),
                        fmt(r["local_target_best_min"]),
                        fmt(r["delta_min"]),
                        fmt(r["delta_pct"], 2),
                        f"{r['target_met_runs']}/{r['runs']}",
                        fmt(r["local_best_val_loss"], 4),
                        str(r["description"]),
                        str(r["paths"]),
                    ]
                    for r in rerun_comparisons
                ],
            )
        )
        lines.append("")
    if failed_runs:
        lines.append("## Failed Local Attempts")
        lines.append("")
        lines.append(
            markdown_table(
                ["label", "track", "error_type", "reason", "path"],
                [[r.label, r.track, r.error_type, r.reason, r.path] for r in failed_runs],
            )
        )
        lines.append("")
    lines.append("## README Top Techniques")
    lines.append("")
    lines.append(markdown_table(["#", "technique"], [[str(i + 1), t["technique"]] for i, t in enumerate(techniques)]))
    lines.append("")
    lines.append("## Short Track Comparison")
    lines.append("")
    short_rows = [r for r in records if r.track == "track_1_short"]
    lines.append(
        markdown_table(
            [
                "#",
                "date",
                "README min",
                "parsed log min",
                "delta %",
                "val_loss",
                "availability",
                "description",
            ],
            [
                [
                    r.record_number,
                    r.date,
                    fmt(r.record_time_min),
                    fmt(r.parsed_log_train_time_min),
                    fmt(r.parsed_log_train_time_delta_pct, 2),
                    fmt(r.parsed_log_val_loss, 4),
                    r.availability,
                    r.description_text,
                ]
                for r in short_rows
            ],
        )
    )
    lines.append("")
    lines.append("## Medium Track Comparison")
    lines.append("")
    medium_rows = [r for r in records if r.track == "track_2_medium"]
    lines.append(
        markdown_table(
            ["#", "date", "README min", "parsed log min", "delta %", "val_loss", "availability", "description"],
            [
                [
                    r.record_number,
                    r.date,
                    fmt(r.record_time_min),
                    fmt(r.parsed_log_train_time_min),
                    fmt(r.parsed_log_train_time_delta_pct, 2),
                    fmt(r.parsed_log_val_loss, 4),
                    r.availability,
                    r.description_text,
                ]
                for r in medium_rows
            ],
        )
    )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- `parsed log min` is the fastest parsed target-meeting log under the README-linked file or directory. For rows with a direct file link, it is that file."
    )
    lines.append("- `rerun_completed` means a local log in `logs/` matches the record's step count or the current root run.")
    lines.append("- Failed local attempts are attempts that exited before emitting any validation result; they are not counted as completed reruns.")
    lines.append("- Rows marked `readme_only` lack both a parsed local log and a runnable code snapshot in this checkout.")
    lines.append("")
    (RESULTS_DIR / "comparison.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records = parse_readme_records()
    logs = scan_logs()
    failed_runs = scan_failed_local_runs()
    attach_log_results(records, logs)
    reruns = summarize_local_reruns(logs)
    techniques = parse_top_techniques()

    write_csv(RESULTS_DIR / "readme_records.csv", records)
    write_csv(RESULTS_DIR / "log_results.csv", logs)
    write_csv(RESULTS_DIR / "local_reruns.csv", reruns)
    write_csv(RESULTS_DIR / "local_vs_readme.csv", build_local_rerun_comparisons(records, reruns))
    write_csv(RESULTS_DIR / "failed_local_runs.csv", failed_runs)
    write_csv(RESULTS_DIR / "top_techniques.csv", techniques)
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(
            {
                "readme_records": len(records),
                "log_results": len(logs),
                "local_rerun_groups": len(reruns),
                "failed_local_runs": len(failed_runs),
                "top_techniques": len(techniques),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_report(records, logs, reruns, failed_runs, techniques)


if __name__ == "__main__":
    main()
