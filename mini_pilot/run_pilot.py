#!/usr/bin/env python3
import csv
import subprocess
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.csv"
SEED_METADATA = ROOT / "seed_metadata.csv"
RESULTS = ROOT / "results.csv"
SEED_RESULTS = ROOT / "seed_results.csv"
SUMMARY_BY_CLASS = ROOT / "summary_by_class.csv"
SUMMARY_BY_STRATUM = ROOT / "summary_by_stratum.csv"
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
    if "time out" in output.lower():
        return "verification timed out"
    if "verified, 0 errors" in output:
        return "verified cleanly"
    return ""


def load_csv(path: Path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_float(value):
    return f"{value:.3f}"


def format_ratio(numerator, denominator):
    if denominator == 0:
        return "NA"
    return format_float(numerator / denominator)


def classify_manifest_row(row):
    transformed_path = row.get("transformed_path", "").strip()
    if not transformed_path:
        return "excluded", "missing transformed_path"
    full_path = ROOT.parent / transformed_path
    if not full_path.exists():
        return "excluded", "transformed file missing"
    return "ready", ""


def compute_summary_rows(group_key, rows):
    grouped = Counter(r[group_key] for r in rows)
    grouped_eval = Counter(r[group_key] for r in rows if r["b1_outcome"] != "excluded")
    grouped_broken = Counter(r[group_key] for r in rows if r["b1_outcome"] == "fail")
    grouped_timeout = Counter(r[group_key] for r in rows if r["b1_outcome"] == "timeout")
    grouped_b2_run = Counter(r[group_key] for r in rows if r["b2_outcome"] not in {"not_run", ""})
    grouped_b2_recovered = Counter(r[group_key] for r in rows if r["b2_outcome"] == "pass")
    summary = []
    for key in sorted(grouped):
        attempted = grouped[key]
        eval_ready = grouped_eval.get(key, 0)
        broken = grouped_broken.get(key, 0)
        timeout = grouped_timeout.get(key, 0)
        b2_run = grouped_b2_run.get(key, 0)
        b2_recovered = grouped_b2_recovered.get(key, 0)
        residual = broken - b2_recovered
        summary.append(
            {
                group_key: key,
                "attempted": attempted,
                "eval_ready": eval_ready,
                "broken_b1": broken,
                "timeout_b1": timeout,
                "b2_run": b2_run,
                "b2_recovered": b2_recovered,
                "residual_after_b2": residual,
                "breakage_rate": format_ratio(broken, attempted),
                "recovery_rate_b2_over_broken": format_ratio(b2_recovered, broken),
            }
        )
    return summary


def main():
    seed_rows = []
    for row in load_csv(SEED_METADATA):
        seed_path = ROOT / "seeds" / row["seed_file"]
        outcome, elapsed, output = run_dafny_verify(seed_path)
        seed_rows.append(
            {
                **row,
                "seed_verify_outcome": outcome,
                "seed_verify_time_sec": format_float(elapsed),
                "seed_verify_reason": short_reason(output),
            }
        )

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
    for row in load_csv(MANIFEST):
        manifest_state, manifest_reason = classify_manifest_row(row)
        b1_outcome = manifest_state
        b1_time = ""
        b1_reason = manifest_reason
        b2_outcome = "not_run"
        b2_time = ""
        b2_reason = ""

        if manifest_state == "ready":
            transformed = ROOT.parent / row["transformed_path"]
            b1_outcome, elapsed, output = run_dafny_verify(transformed)
            b1_time = format_float(elapsed)
            b1_reason = short_reason(output)

            b2_path = row.get("b2_path", "").strip()
            if b1_outcome in {"fail", "timeout"} and b2_path:
                b2_file = ROOT.parent / b2_path
                if b2_file.exists():
                    b2_outcome, b2_elapsed, b2_output = run_dafny_verify(b2_file)
                    b2_time = format_float(b2_elapsed)
                    b2_reason = short_reason(b2_output)
                else:
                    b2_outcome = "excluded"
                    b2_reason = "b2 file missing"

        failure_label = row["failure_mode_label"]
        if b1_outcome in {"pass", "excluded"}:
            failure_label = "not_applicable"
        elif failure_label == "not_applicable":
            failure_label = "unexplained_or_tool_sensitive_failure"

        result_rows.append(
            {
                "seed_id": row["seed_id"],
                "seed_source": row["seed_source"],
                "seed_stratum": row["seed_stratum"],
                "refactoring_class": row["refactoring_class"],
                "transformation_id": row["transformation_id"],
                "b1_outcome": b1_outcome,
                "b2_outcome": b2_outcome,
                "b3_outcome": "not_run",
                "failure_mode_label": failure_label,
                "verifier_time_b1": b1_time,
                "verifier_time_b2": b2_time,
                "retry_count_b3": "",
                "token_cost_b3": "",
                "notes": row["notes"],
                "b1_reason": b1_reason,
                "b2_reason": b2_reason,
            }
        )

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

    write_csv(
        SUMMARY_BY_CLASS,
        compute_summary_rows("refactoring_class", result_rows),
        [
            "refactoring_class",
            "attempted",
            "eval_ready",
            "broken_b1",
            "timeout_b1",
            "b2_run",
            "b2_recovered",
            "residual_after_b2",
            "breakage_rate",
            "recovery_rate_b2_over_broken",
        ],
    )
    write_csv(
        SUMMARY_BY_STRATUM,
        compute_summary_rows("seed_stratum", result_rows),
        [
            "seed_stratum",
            "attempted",
            "eval_ready",
            "broken_b1",
            "timeout_b1",
            "b2_run",
            "b2_recovered",
            "residual_after_b2",
            "breakage_rate",
            "recovery_rate_b2_over_broken",
        ],
    )

    n_items = len(result_rows)
    n_eval = sum(1 for r in result_rows if r["b1_outcome"] != "excluded")
    broken_rows = [r for r in result_rows if r["b1_outcome"] == "fail"]
    timeout_rows = [r for r in result_rows if r["b1_outcome"] == "timeout"]
    excluded_rows = [r for r in result_rows if r["b1_outcome"] == "excluded"]
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

    b1_times = [float(r["verifier_time_b1"]) for r in result_rows if r["verifier_time_b1"]]
    b2_times = [float(r["verifier_time_b2"]) for r in result_rows if r["verifier_time_b2"]]
    avg_b1 = sum(b1_times) / len(b1_times) if b1_times else 0.0
    avg_b2 = sum(b2_times) / len(b2_times) if b2_times else 0.0

    sparse_classes = sorted(cls for cls, count in class_attempts.items() if count < 3)
    sparse_labels = sorted(label for label, count in label_broken.items() if count < 2)

    metrics_ready = "ready" if n_items >= 24 and n_broken > 0 and not timeout_rows else "mostly_ready"
    outcome_vocab_ready = "ready" if excluded_rows or timeout_rows or n_items >= 24 else "mostly_ready"
    label_ready = "ready" if len(label_broken) >= 2 else "not_ready"
    table_shapes_ready = "ready" if len(stratum_item_count) >= 2 and not sparse_classes else "mostly_ready"

    lines = []
    lines.append("# Mini-Pilot Memo")
    lines.append("")
    lines.append("## What Was Run")
    lines.append("")
    lines.append(f"- Seeds verified locally: {sum(1 for r in seed_rows if r['seed_verify_outcome'] == 'pass')}/{len(seed_rows)}")
    lines.append(f"- Transformed items attempted: {n_items}")
    lines.append(f"- Eval-ready items: {n_eval}")
    lines.append(f"- Broken under B1: {n_broken}")
    lines.append(f"- Timed out under B1: {len(timeout_rows)}")
    lines.append(f"- Excluded before evaluation: {len(excluded_rows)}")
    lines.append(f"- Recovered by B2: {recovered_b2}")
    lines.append("- B3 status: deferred (`not_run` for all items)")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Seed strata: {', '.join(sorted(stratum_seed_count))}")
    lines.append(f"- Refactoring classes: {', '.join(sorted(class_attempts))}")
    lines.append(
        "- Failure labels observed on broken items: "
        + (", ".join(sorted(label_broken)) if label_broken else "none")
    )
    lines.append("")
    lines.append("## Metric Check")
    lines.append("")
    lines.append(f"- `SR = N_eval / N_items = {n_eval}/{n_items} = {format_ratio(n_eval, n_items)}`")
    lines.append(
        f"- `RR(B1) = 0/{n_broken} = {format_ratio(0, n_broken)}` because the broken subset is still defined by B1 failures."
    )
    lines.append(f"- `RR(B2) = {recovered_b2}/{n_broken} = {format_ratio(recovered_b2, n_broken)}`")
    lines.append(
        f"- Provisional `Gap_residual` over available baselines (B1/B2 only) = {unresolved_after_b2}/{n_broken} = {format_ratio(unresolved_after_b2, n_broken)}"
    )
    lines.append(f"- `Cost_ver(B1)` mean = {format_float(avg_b1)} seconds")
    lines.append(f"- `Cost_ver(B2)` mean over runs that executed = {format_float(avg_b2)} seconds")
    lines.append("- `Cost_tok(B3)` remains unvalidated because B3 was intentionally deferred.")
    lines.append("")
    lines.append("### Breakage Rate by Refactoring Class")
    lines.append("")
    for cls in sorted(class_attempts):
        attempted = class_attempts[cls]
        broken = class_broken.get(cls, 0)
        recovered = class_recovered_b2.get(cls, 0)
        lines.append(
            f"- `{cls}`: `BR = {broken}/{attempted} = {format_ratio(broken, attempted)}`, `RR(B2|broken) = {recovered}/{broken} = {format_ratio(recovered, broken)}`"
        )
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
            f"| {cls} | {attempted} | {broken} | {format_ratio(broken, attempted)} | {recovered} | {residual} |"
        )
    lines.append("")
    lines.append("### Failure-Mode Preview")
    lines.append("")
    lines.append("| Failure mode | Broken subset | Residual subset |")
    lines.append("| --- | ---: | ---: |")
    for label in sorted(set(label_broken) | set(label_residual)):
        lines.append(f"| {label} | {label_broken.get(label, 0)} | {label_residual.get(label, 0)} |")
    lines.append("")
    lines.append("### Sparse-Cell Warnings")
    lines.append("")
    lines.append(
        f"- Sparse class rows (`attempted < 3`): {', '.join(sparse_classes) if sparse_classes else 'none'}"
    )
    lines.append(
        f"- Sparse failure labels (`broken count < 2`): {', '.join(sparse_labels) if sparse_labels else 'none'}"
    )
    lines.append("")
    lines.append("## Ready / Not Ready")
    lines.append("")
    lines.append(f"- Metric formulas: `{metrics_ready}`")
    lines.append(f"- Outcome vocabulary (`pass/fail/timeout/excluded/not_run`): `{outcome_vocab_ready}`")
    lines.append(f"- Failure-label taxonomy: `{label_ready}`")
    lines.append(f"- Section 5 table shapes: `{table_shapes_ready}`")
    lines.append("")
    lines.append("## What Worked")
    lines.append("")
    lines.append("- `SR`, `BR(class_i)`, and `RR(B2|broken)` remain easy to compute and interpret at the larger pilot scale.")
    lines.append("- Multiple strata now make the composition table meaningfully informative instead of degenerate.")
    lines.append("- The current result schema survives a larger B1/B2-only run without needing paper-side column changes.")
    lines.append("")
    lines.append("## What Was Awkward")
    lines.append("")
    lines.append("- `RR(B1)` is still mechanically zero because B1 constructs the broken subset rather than serving as a genuine recovery baseline.")
    lines.append("- `Gap_residual` still needs an explicit available-baselines convention while B3 remains deferred.")
    lines.append("- Some classes may still be too sparse for a final paper table even if they are useful in a design-validation pilot.")
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
    lines.append("## Decision Output")
    lines.append("")
    lines.append("- Are the current metrics workable? Yes, with two caveats: treat `RR(B1)` as a reporting convention and parameterize `Gap_residual` by available baselines in early experiments.")
    lines.append("- Are the current labels workable? Yes for pilot-scale characterization, though a larger benchmark should continue checking whether low-frequency labels deserve merging.")
    lines.append("- Are the current table shapes workable? Mostly yes, but low-frequency class rows should be monitored before the final paper tables are frozen.")
    lines.append("- What must change before adding B3 or scaling further? Add an explicit `available_baselines` interpretation rule, keep `not_run` first-class in paper tables, and preserve `excluded` separately from true verification failures.")
    lines.append("")
    lines.append("## Recommended Revisions Before Scaling Again")
    lines.append("")
    lines.append("- Keep `not_run` and `excluded` first-class in both CSV outputs and paper-facing tables.")
    lines.append("- Report `RR(B2 | broken)` explicitly and stop treating `RR(B1)` as an informative comparator.")
    lines.append("- Parameterize residual-gap reporting by the baselines actually enabled in the experiment tier.")
    lines.append("- If a class remains sparse after the next scale-up, consider merging or demoting it in Section 5 tables while keeping the raw manifest-level labels intact.")

    MEMO.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
