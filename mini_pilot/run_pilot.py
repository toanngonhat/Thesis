#!/usr/bin/env python3
import csv
import os
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.csv"
SEED_METADATA = ROOT / "seed_metadata.csv"
RESULTS = ROOT / "results.csv"
SEED_RESULTS = ROOT / "seed_results.csv"
MEMO = ROOT / "pilot_memo.md"
TIMEOUT_SECONDS = 60


def run_dafny_verify(path: Path):
    started = time.monotonic()
    try:
        proc = subprocess.run(
            ["dafny", "verify", str(path)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=ROOT.parent,
        )
        elapsed = time.monotonic() - started
        output = (proc.stdout or "") + (proc.stderr or "")
        outcome = "pass" if proc.returncode == 0 else "fail"
        return outcome, elapsed, output
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        output = (exc.stdout or "") + (exc.stderr or "")
        return "timeout", elapsed, output


def short_reason(output: str):
    for line in output.splitlines():
        line = line.strip()
        if "Error:" in line:
            return line.split("Error:", 1)[1].strip()
    if "verified, 0 errors" in output:
        return "verified cleanly"
    return ""


def load_seed_metadata():
    with SEED_METADATA.open() as handle:
        return list(csv.DictReader(handle))


def load_manifest():
    with MANIFEST.open() as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_float(x):
    return f"{x:.3f}"


def main():
    seed_rows = []
    for row in load_seed_metadata():
        seed_path = ROOT / "seeds" / row["seed_file"]
        outcome, elapsed, output = run_dafny_verify(seed_path)
        seed_rows.append({
            **row,
            "seed_verify_outcome": outcome,
            "seed_verify_time_sec": format_float(elapsed),
            "seed_verify_reason": short_reason(output),
        })

    write_csv(
        SEED_RESULTS,
        seed_rows,
        [
            "seed_id",
            "seed_file",
            "seed_source",
            "seed_stratum",
            "proof_profile",
            "license",
            "source_repo",
            "source_path",
            "seed_verify_outcome",
            "seed_verify_time_sec",
            "seed_verify_reason",
        ],
    )

    result_rows = []
    for row in load_manifest():
        transformed = ROOT.parent / row["transformed_path"]
        b1_outcome, b1_time, b1_output = run_dafny_verify(transformed)
        transformed_reason = short_reason(b1_output)

        b2_outcome = "not_run"
        b2_time = ""
        b2_reason = ""
        if b1_outcome != "pass" and row["b2_path"]:
            b2_path = ROOT.parent / row["b2_path"]
            b2_outcome, b2_elapsed, b2_output = run_dafny_verify(b2_path)
            b2_time = format_float(b2_elapsed)
            b2_reason = short_reason(b2_output)

        failure_label = row["failure_mode_label"]
        if b1_outcome == "pass":
            failure_label = "not_applicable"

        result_rows.append({
            "seed_id": row["seed_id"],
            "seed_source": row["seed_source"],
            "seed_stratum": row["seed_stratum"],
            "refactoring_class": row["refactoring_class"],
            "transformation_id": row["transformation_id"],
            "b1_outcome": b1_outcome,
            "b2_outcome": b2_outcome,
            "b3_outcome": "not_run",
            "failure_mode_label": failure_label,
            "verifier_time_b1": format_float(b1_time),
            "verifier_time_b2": b2_time,
            "retry_count_b3": "",
            "token_cost_b3": "",
            "notes": row["notes"],
            "b1_reason": transformed_reason,
            "b2_reason": b2_reason,
        })

    write_csv(
        RESULTS,
        result_rows,
        [
            "seed_id",
            "seed_source",
            "seed_stratum",
            "refactoring_class",
            "transformation_id",
            "b1_outcome",
            "b2_outcome",
            "b3_outcome",
            "failure_mode_label",
            "verifier_time_b1",
            "verifier_time_b2",
            "retry_count_b3",
            "token_cost_b3",
            "notes",
            "b1_reason",
            "b2_reason",
        ],
    )

    n_items = len(result_rows)
    n_eval = sum(1 for r in result_rows if r["b1_outcome"] != "excluded")
    broken_rows = [r for r in result_rows if r["b1_outcome"] == "fail"]
    n_broken = len(broken_rows)
    recovered_b2 = sum(1 for r in broken_rows if r["b2_outcome"] == "pass")
    unresolved_after_b2 = sum(1 for r in broken_rows if r["b2_outcome"] != "pass")
    class_attempts = Counter(r["refactoring_class"] for r in result_rows)
    class_broken = Counter(r["refactoring_class"] for r in broken_rows)
    class_recovered_b2 = Counter(r["refactoring_class"] for r in broken_rows if r["b2_outcome"] == "pass")
    label_broken = Counter(r["failure_mode_label"] for r in broken_rows if r["failure_mode_label"] != "not_applicable")
    label_residual = Counter(
        r["failure_mode_label"]
        for r in broken_rows
        if r["b2_outcome"] != "pass" and r["failure_mode_label"] != "not_applicable"
    )
    stratum_seed_count = Counter(r["seed_stratum"] for r in seed_rows)
    stratum_item_count = Counter(r["seed_stratum"] for r in result_rows)
    stratum_eval_count = Counter(r["seed_stratum"] for r in result_rows if r["b1_outcome"] != "excluded")

    avg_b1 = sum(float(r["verifier_time_b1"]) for r in result_rows) / len(result_rows)
    b2_ran = [float(r["verifier_time_b2"]) for r in result_rows if r["verifier_time_b2"]]
    avg_b2 = sum(b2_ran) / len(b2_ran) if b2_ran else 0.0

    lines = []
    lines.append("# Mini-Pilot Memo")
    lines.append("")
    lines.append("## What Was Run")
    lines.append("")
    lines.append(f"- Seeds verified locally: {sum(1 for r in seed_rows if r['seed_verify_outcome'] == 'pass')}/{len(seed_rows)}")
    lines.append(f"- Transformed items evaluated: {n_items}")
    lines.append(f"- Broken under B1: {n_broken}")
    lines.append(f"- Recovered by B2: {recovered_b2}")
    lines.append(f"- B3 status: deferred (`not_run` for all items)")
    lines.append("")
    lines.append("## Metric Check")
    lines.append("")
    lines.append(f"- `SR = N_eval / N_items = {n_eval}/{n_items} = {format_float(n_eval / n_items)}`")
    lines.append(f"- `RR(B1) = 0/{n_broken} = {format_float(0.0 if n_broken else 0.0)}` because the broken subset is defined by B1 failures.")
    lines.append(f"- `RR(B2) = {recovered_b2}/{n_broken} = {format_float(recovered_b2 / n_broken) if n_broken else 'NA'}`")
    lines.append(f"- `Gap_residual` over available baselines (B1/B2 only in this pilot) = {unresolved_after_b2}/{n_broken} = {format_float(unresolved_after_b2 / n_broken) if n_broken else 'NA'}`")
    lines.append(f"- `Cost_ver(B1)` mean = {format_float(avg_b1)} seconds")
    lines.append(f"- `Cost_ver(B2)` mean over runs that actually executed = {format_float(avg_b2)} seconds")
    lines.append("- `Cost_tok(B3)` could not be instantiated because B3 was intentionally deferred.")
    lines.append("")
    lines.append("### Breakage Rate by Refactoring Class")
    lines.append("")
    for cls in sorted(class_attempts):
        attempted = class_attempts[cls]
        broken = class_broken.get(cls, 0)
        lines.append(f"- `{cls}`: `BR = {broken}/{attempted} = {format_float(broken / attempted)}`")
    lines.append("")
    lines.append("## Table Stress Test")
    lines.append("")
    lines.append("### Benchmark Composition Preview")
    lines.append("")
    lines.append("| Stratum | Seeds | Items | Eval-ready |")
    lines.append("| --- | ---: | ---: | ---: |")
    for stratum in sorted(stratum_item_count):
        lines.append(
            f"| {stratum} | {stratum_seed_count.get(stratum, 0)} | {stratum_item_count[stratum]} | {stratum_eval_count.get(stratum, 0)} |"
        )
    lines.append("")
    lines.append("### Breakage / Recovery Preview")
    lines.append("")
    lines.append("| Class | Attempted | Broken | BR | Recovered by B2 | Residual after B2 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for cls in sorted(class_attempts):
        attempted = class_attempts[cls]
        broken = class_broken.get(cls, 0)
        recovered = class_recovered_b2.get(cls, 0)
        residual = broken - recovered
        lines.append(
            f"| {cls} | {attempted} | {broken} | {format_float(broken / attempted)} | {recovered} | {residual} |"
        )
    lines.append("")
    lines.append("### Failure-Mode Preview")
    lines.append("")
    lines.append("| Failure mode | Broken subset | Residual subset |")
    lines.append("| --- | ---: | ---: |")
    for label in sorted(set(label_broken) | set(label_residual)):
        lines.append(
            f"| {label} | {label_broken.get(label, 0)} | {label_residual.get(label, 0)} |"
        )
    lines.append("")
    lines.append("- Benchmark composition table: structurally works, but with one seed stratum the current paper table is wider than the pilot data really needs.")
    lines.append("- Breakage/recovery table: works and is informative even at mini scale; sparse rows are acceptable, but a `not_run` convention is necessary for B3.")
    lines.append("- Failure-mode table: works, but pass cases need an explicit `not_applicable` convention outside the broken subset.")
    lines.append("")
    lines.append("## What Worked")
    lines.append("")
    lines.append("- `SR`, `BR(class_i)`, and `RR(B2)` were easy to compute and interpret.")
    lines.append("- Distinguishing `pass`, `fail`, and `not_run` was enough for a first pilot.")
    lines.append("- The current failure labels were assignable on the broken subset.")
    lines.append("")
    lines.append("## What Was Awkward")
    lines.append("")
    lines.append("- `RR(B1)` is mechanically zero once the broken subset is defined by B1, so it is more a reporting convention than an informative comparison.")
    lines.append("- `Gap_residual` becomes ambiguous when B3 is deferred. For the pilot we computed the gap over available baselines and flagged the mismatch with the paper formula.")
    lines.append("- `Cost_tok(B3)` cannot be validated without at least one real B3 run.")
    lines.append("")
    lines.append("## Failure-Mode Distribution")
    lines.append("")
    for label in sorted(label_broken):
        lines.append(f"- Broken subset `{label}`: {label_broken[label]}")
    lines.append("")
    lines.append("## Residual Failure-Mode Distribution")
    lines.append("")
    for label in sorted(label_residual):
        lines.append(f"- Residual subset `{label}`: {label_residual[label]}")
    lines.append("")
    lines.append("## Recommended Revisions Before Scaling")
    lines.append("")
    lines.append("- Add an explicit `available_baselines` or `b3_enabled` flag when computing the residual gap in early experiments.")
    lines.append("- Treat `not_run` as a first-class outcome in tables rather than forcing empty cells.")
    lines.append("- Keep `excluded` separate from `fail`, even though this pilot did not produce exclusions.")
    lines.append("- Consider reporting `RR(B2 | broken)` and treating B1 primarily as the broken-subset constructor rather than as a recovery baseline.")

    MEMO.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
