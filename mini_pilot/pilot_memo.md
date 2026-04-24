# Mini-Pilot Memo

## What Was Run

- Seeds verified locally: 8/8
- Transformed items attempted: 24
- Eval-ready items: 24
- Broken under B1: 9
- Timed out under B1: 0
- Excluded before evaluation: 0
- Recovered by B2: 4
- B3 status: deferred (`not_run` for all items)

## Coverage

- Seed strata: benchmark_example_suite, proof_engineering_case
- Refactoring classes: ghost_code_movement, helper_extraction, rename, statement_reordering
- Failure labels observed on broken items: brittle_lemma_or_helper_application_structure, broken_assertion_flow, ghost_code_or_proof_hint_displacement, weakened_loop_invariants

## Metric Check

- `SR = N_eval / N_items = 24/24 = 1.000`
- `RR(B1) = 0/9 = 0.000` because the broken subset is still defined by B1 failures.
- `RR(B2) = 4/9 = 0.444`
- Provisional `Gap_residual` over available baselines (B1/B2 only) = 5/9 = 0.556
- `Cost_ver(B1)` mean = 1.299 seconds
- `Cost_ver(B2)` mean over runs that executed = 1.064 seconds
- `Cost_tok(B3)` remains unvalidated because B3 was intentionally deferred.

### Breakage Rate by Refactoring Class

- `ghost_code_movement`: `BR = 2/3 = 0.667`, `RR(B2|broken) = 0/2 = 0.000`
- `helper_extraction`: `BR = 7/8 = 0.875`, `RR(B2|broken) = 4/7 = 0.571`
- `rename`: `BR = 0/8 = 0.000`, `RR(B2|broken) = 0/0 = NA`
- `statement_reordering`: `BR = 0/5 = 0.000`, `RR(B2|broken) = 0/0 = NA`

## Table Stress Test

### Benchmark Composition Preview

| Stratum | Seeds | Items | Eval-ready |
| --- | ---: | ---: | ---: |
| benchmark_example_suite | 5 | 15 | 15 |
| proof_engineering_case | 3 | 9 | 9 |

### Breakage / Recovery Preview

| Class | Attempted | Broken | BR | Recovered by B2 | Residual after B2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ghost_code_movement | 3 | 2 | 0.667 | 0 | 2 |
| helper_extraction | 8 | 7 | 0.875 | 4 | 3 |
| rename | 8 | 0 | 0.000 | 0 | 0 |
| statement_reordering | 5 | 0 | 0.000 | 0 | 0 |

### Failure-Mode Preview

| Failure mode | Broken subset | Residual subset |
| --- | ---: | ---: |
| brittle_lemma_or_helper_application_structure | 3 | 1 |
| broken_assertion_flow | 1 | 1 |
| ghost_code_or_proof_hint_displacement | 4 | 3 |
| weakened_loop_invariants | 1 | 0 |

### Sparse-Cell Warnings

- Sparse class rows (`attempted < 3`): none
- Sparse failure labels (`broken count < 2`): broken_assertion_flow, weakened_loop_invariants

## Ready / Not Ready

- Metric formulas: `ready`
- Outcome vocabulary (`pass/fail/timeout/excluded/not_run`): `ready`
- Failure-label taxonomy: `ready`
- Section 5 table shapes: `ready`

## What Worked

- `SR`, `BR(class_i)`, and `RR(B2|broken)` remain easy to compute and interpret at the larger pilot scale.
- Multiple strata now make the composition table meaningfully informative instead of degenerate.
- The current result schema survives a larger B1/B2-only run without needing paper-side column changes.

## What Was Awkward

- `RR(B1)` is still mechanically zero because B1 constructs the broken subset rather than serving as a genuine recovery baseline.
- `Gap_residual` still needs an explicit available-baselines convention while B3 remains deferred.
- Some classes may still be too sparse for a final paper table even if they are useful in a design-validation pilot.

## Failure-Mode Distribution

- Broken subset `brittle_lemma_or_helper_application_structure`: 3
- Broken subset `broken_assertion_flow`: 1
- Broken subset `ghost_code_or_proof_hint_displacement`: 4
- Broken subset `weakened_loop_invariants`: 1

## Residual Failure-Mode Distribution

- Residual subset `brittle_lemma_or_helper_application_structure`: 1
- Residual subset `broken_assertion_flow`: 1
- Residual subset `ghost_code_or_proof_hint_displacement`: 3

## Decision Output

- Are the current metrics workable? Yes, with two caveats: treat `RR(B1)` as a reporting convention and parameterize `Gap_residual` by available baselines in early experiments.
- Are the current labels workable? Yes for pilot-scale characterization, though a larger benchmark should continue checking whether low-frequency labels deserve merging.
- Are the current table shapes workable? Mostly yes, but low-frequency class rows should be monitored before the final paper tables are frozen.
- What must change before adding B3 or scaling further? Add an explicit `available_baselines` interpretation rule, keep `not_run` first-class in paper tables, and preserve `excluded` separately from true verification failures.

## Recommended Revisions Before Scaling Again

- Keep `not_run` and `excluded` first-class in both CSV outputs and paper-facing tables.
- Report `RR(B2 | broken)` explicitly and stop treating `RR(B1)` as an informative comparator.
- Parameterize residual-gap reporting by the baselines actually enabled in the experiment tier.
- If a class remains sparse after the next scale-up, consider merging or demoting it in Section 5 tables while keeping the raw manifest-level labels intact.
