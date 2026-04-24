# `mini_pilot`

Broader realistic Dafny pilot for checking whether the current P1 metrics, formulas, and result tables behave sensibly before a full Dataset~A pipeline exists.

## Contents

- `seeds/`: eight copied seeds from the official `dafny-lang/dafny` repository
- `transformed/`: manually created semantics-preserving refactoring variants
- `b2/`: lightweight B2-style follow-up variants for broken transformed items
- `seed_metadata.csv`: provenance and seed-role metadata
- `manifest.csv`: one row per transformed item
- `run_pilot.py`: runs Dafny verification and materializes the pilot results
- `seed_results.csv`: seed verification outcomes
- `results.csv`: one row per transformed item with B1/B2/B3 outcome fields
- `summary_by_class.csv`: derived class-level breakage and recovery summary
- `summary_by_stratum.csv`: derived stratum-level breakage and recovery summary
- `pilot_memo.md`: short interpretation memo on what the metrics did and did not capture cleanly
- `LICENSE.dafny-repo.txt`: copied MIT license from the upstream Dafny repository

## Seed Set

The pilot uses eight official examples from `dafny-lang/dafny` across two strata:

- `benchmark_example_suite`: `summax`, `invert`, `findzero`, `queens`, `deque`
- `proof_engineering_case`: `twowaysort`, `ringbuffer`, `bfs`

These seeds cover loop invariants, quantified search invariants, dynamic frames, ghost-state reasoning, sequence views, and graph reachability. All eight verify on local Dafny `4.11.0`.

## Refactoring Classes Used

- `rename`
- `helper_extraction`
- `statement_reordering`
- `ghost_code_movement`

The pilot contains 24 transformed items in total. B3 is intentionally deferred in this breadth-focused pass, so `b3_outcome` is recorded as `not_run`.

## Run

From the repo root:

```bash
python3 mini_pilot/run_pilot.py
```

This regenerates:

- `mini_pilot/seed_results.csv`
- `mini_pilot/results.csv`
- `mini_pilot/summary_by_class.csv`
- `mini_pilot/summary_by_stratum.csv`
- `mini_pilot/pilot_memo.md`
