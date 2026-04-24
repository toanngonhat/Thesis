# Mini-Pilot Memo

## What Was Run

- Seeds verified locally: 3/3
- Transformed items evaluated: 9
- Broken under B1: 3
- Recovered by B2: 2
- B3 status: deferred (`not_run` for all items)

## Metric Check

- `SR = N_eval / N_items = 9/9 = 1.000`
- `RR(B1) = 0/3 = 0.000` because the broken subset is defined by B1 failures.
- `RR(B2) = 2/3 = 0.667`
- `Gap_residual` over available baselines (B1/B2 only in this pilot) = 1/3 = 0.333`
- `Cost_ver(B1)` mean = 1.002 seconds
- `Cost_ver(B2)` mean over runs that actually executed = 1.029 seconds
- `Cost_tok(B3)` could not be instantiated because B3 was intentionally deferred.

### Breakage Rate by Refactoring Class

- `ghost_code_movement`: `BR = 1/1 = 1.000`
- `helper_extraction`: `BR = 2/3 = 0.667`
- `rename`: `BR = 0/3 = 0.000`
- `statement_reordering`: `BR = 0/2 = 0.000`

## Table Stress Test

### Benchmark Composition Preview

| Stratum | Seeds | Items | Eval-ready |
| --- | ---: | ---: | ---: |
| benchmark_example_suite | 3 | 9 | 9 |

### Breakage / Recovery Preview

| Class | Attempted | Broken | BR | Recovered by B2 | Residual after B2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ghost_code_movement | 1 | 1 | 1.000 | 0 | 1 |
| helper_extraction | 3 | 2 | 0.667 | 2 | 0 |
| rename | 3 | 0 | 0.000 | 0 | 0 |
| statement_reordering | 2 | 0 | 0.000 | 0 | 0 |

### Failure-Mode Preview

| Failure mode | Broken subset | Residual subset |
| --- | ---: | ---: |
| brittle_lemma_or_helper_application_structure | 1 | 0 |
| ghost_code_or_proof_hint_displacement | 2 | 1 |

- Benchmark composition table: structurally works, but with one seed stratum the current paper table is wider than the pilot data really needs.
- Breakage/recovery table: works and is informative even at mini scale; sparse rows are acceptable, but a `not_run` convention is necessary for B3.
- Failure-mode table: works, but pass cases need an explicit `not_applicable` convention outside the broken subset.

## What Worked

- `SR`, `BR(class_i)`, and `RR(B2)` were easy to compute and interpret.
- Distinguishing `pass`, `fail`, and `not_run` was enough for a first pilot.
- The current failure labels were assignable on the broken subset.

## What Was Awkward

- `RR(B1)` is mechanically zero once the broken subset is defined by B1, so it is more a reporting convention than an informative comparison.
- `Gap_residual` becomes ambiguous when B3 is deferred. For the pilot we computed the gap over available baselines and flagged the mismatch with the paper formula.
- `Cost_tok(B3)` cannot be validated without at least one real B3 run.

## Failure-Mode Distribution

- Broken subset `brittle_lemma_or_helper_application_structure`: 1
- Broken subset `ghost_code_or_proof_hint_displacement`: 2

## Residual Failure-Mode Distribution

- Residual subset `ghost_code_or_proof_hint_displacement`: 1

## Recommended Revisions Before Scaling

- Add an explicit `available_baselines` or `b3_enabled` flag when computing the residual gap in early experiments.
- Treat `not_run` as a first-class outcome in tables rather than forcing empty cells.
- Keep `excluded` separate from `fail`, even though this pilot did not produce exclusions.
- Consider reporting `RR(B2 | broken)` and treating B1 primarily as the broken-subset constructor rather than as a recovery baseline.
