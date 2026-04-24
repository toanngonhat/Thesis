# P1 Outline

This outline maps each section to the claims and evidence in **Project P1** of [../revised_plan.md](../revised_plan.md).

## Core claim

Semantics-preserving refactorings in Dafny break verification often enough, and in consistent enough ways, that simple baselines leave a meaningful residual problem for later repair systems.

## Benchmark philosophy

P1 should read as a reusable dataset-and-evaluation paper even before any advanced repair engine exists. The benchmark itself, the failure taxonomy, and the baseline-derived residual gap are all first-class contributions, not just setup for later work.

## Section mapping

### `01_intro.tex`

- State the practical problem: verified code evolves, but proofs are brittle under maintenance.
- Introduce the specific lens of semantics-preserving refactoring.
- Preview the paper contributions:
  - a Dafny refactoring benchmark;
  - an empirical characterization of proof brittleness;
  - a baseline comparison for recovery.

### `02_background.tex`

- Explain proof maintenance and why refactoring-induced breakage matters.
- Position Dafny as the chosen ecosystem for a focused empirical study.
- Define what counts as a semantics-preserving refactoring in this paper.

### `03_dataset_and_refactorings.tex`

- Describe Dataset A and the seed-program sources.
- Document the seven refactoring classes:
  - rename;
  - helper extraction;
  - inlining;
  - legal statement reordering;
  - non-behavioral loop reshaping;
  - contract factoring;
  - ghost-code movement.
- Explain benchmark construction, replay harness, and metadata logging.

### `04_baselines_and_setup.tex`

- Define B1 re-verification, B2 syntactic transfer, and B3 LLM-only repair precisely.
- Record verifier version, timeout budget, and cost logging policy.
- State the evaluation metrics and the success threshold from P1.

### `05_results.tex`

- Report breakage rate per refactoring class.
- Report recovery rate for B1/B2/B3 with confidence intervals.
- Analyze verifier cost and LLM cost.
- Summarize the failure-mode taxonomy and residual gap for P2.

### `06_threats_to_validity.tex`

- Discuss seed-program representativeness.
- Discuss synthetic refactoring realism.
- Discuss prompt and model sensitivity for B3.
- Discuss limits of generalizing from Dafny to other verifier families.

### `07_related_work.tex`

- Connect to refactoring literature.
- Connect to software maintenance and proof engineering.
- Connect to LLM-based repair and program repair baselines.

### `08_conclusion.tex`

- Restate the paper's empirical findings.
- Make the handoff to Project P2 explicit:
  - why the benchmark matters;
  - what baseline gap remains to be addressed.

### `appendix_artifact.tex`

- Include environment setup, directory layout, and replay instructions.
- Document artifact contents and anonymization considerations.

### `appendix_prompt.tex`

- Include the exact B3 prompt template.
- Include the retry policy, acceptance rule, and logging fields.
