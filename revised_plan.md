# Split Thesis Plan: Refactoring-Stable Proof Repair as Three Publishable Units

## 1. Goal of this revision

This plan keeps the central research idea:

> Proof maintenance should be treated as semantic repair over related program versions, not as proof synthesis from scratch.

But it decomposes the work into **three self-contained projects**, each designed to:

- stand alone as a publishable artifact at a CORE rank B venue;
- feed the next project with a concrete, reusable dependency;
- leave the full thesis defensible even if only the first two land.

Design principle:

> one shared ecosystem (Dafny), one shared benchmark spine, three papers with non-overlapping claims.

## 2. Shared assumptions across all projects

- **Verifier**: Dafny (subject to the Month-1 pilot in §8 confirming sufficient real-history data; fallback is Verus).
- **Proof-checked validation**: every claimed repair must re-verify under a declared per-candidate time budget (default 60s, logged as a hyperparameter).
- **Reproducibility**: each project ships a Docker image, a pinned toolchain, and a CI harness that replays the reported numbers. This is a hard deliverable, not an appendix.
- **Licensing**: mined real-history artifacts are restricted to permissively licensed repositories; license is recorded per pair.

## 3. Project overview and dependencies

| ID | Title | Primary claim | Depends on |
| -- | ----- | ------------- | ---------- |
| **P1** | Brittleness under refactoring: a Dafny benchmark and empirical study | Semantics-preserving refactorings break proofs frequently and in characterizable ways; simple baselines recover only a fraction. | — |
| **P2** | Structured symbolic repair for Dafny proofs | Alignment-plus-operator repair beats syntactic transfer and re-verification under matched compute. | P1 benchmark |
| **P3** | Hybrid LLM-symbolic repair with brittleness/drift triage | Narrow LLM candidates plus a repair-vs-escalate classifier improve end-to-end repair without sacrificing soundness. | P1 benchmark, P2 system |

The three projects also compose into a coherent thesis (§10).

---

## 4. Project P1 — Brittleness under refactoring: a Dafny benchmark and empirical study

### 4.1 Claim

Semantics-preserving refactorings on verified Dafny programs cause proof breakage at a substantial, measurable rate, with failure modes that cluster into a small number of categories. Existing recovery strategies (re-verification, syntactic transfer, off-the-shelf LLM repair) leave a large residual gap.

### 4.2 Research questions

- **RQ1.1** What fraction of semantics-preserving refactorings break verification on a curated Dafny corpus?
- **RQ1.2** Which refactoring classes dominate breakage, and which proof artifacts (assertions, invariants, triggers, lemma calls) are most often affected?
- **RQ1.3** How much of the breakage is recovered by three simple baselines: re-run, syntactic transfer, and a standardized LLM-only prompt?

### 4.3 Scope

- Build a **refactoring engine** for Dafny that applies a fixed catalog of seven semantics-preserving transformations: rename, helper extraction, inlining, legal statement reordering, non-behavioral loop reshaping, contract factoring, ghost-code movement.
- Build **Dataset A**: 250–500 verified seed programs × applicable refactorings, yielding ~1.5–3k version pairs. Seeds drawn from Dafny tutorials, textbook examples, `dafny-lang/libraries`, `IronFleet`, and `Dafny-VMC`.
- Run the three baselines and report breakage rate, recovery rate, cost.

### 4.4 Baselines

- **B1 Re-verification**: run Dafny on the evolved program unchanged.
- **B2 Syntactic transfer**: rename- and diff-aware textual transfer of old annotations.
- **B3 LLM-only repair**: fully specified — model `claude-sonnet-4-6`, temperature 0.2, up to 5 retries with verifier error fed back, 200k-context single-turn, per-task cost ceiling logged. Only proof-checked outputs count as success.

### 4.5 Metrics and success threshold

- **M1.1** Breakage rate per refactoring class (descriptive).
- **M1.2** Recovery rate per baseline, with bootstrap 95% CIs.
- **M1.3** Cost: verifier wall-clock and LLM token spend per attempt.
- **Success**: (a) breakage rate ≥ 20% on at least three refactoring classes; (b) no baseline exceeds 70% recovery on Dataset A — i.e., there is a real residual problem for P2 to attack.

### 4.6 Deliverables

1. Refactoring engine (open source).
2. Dataset A with reproducible construction scripts.
3. Empirical paper with failure-mode taxonomy.

### 4.7 Target venues

- Primary: **SANER**, **ICSME**, **MSR** (data showcase), **ESEM**.
- Secondary: **EASE**, **SCAM**, **ICPC**.

### 4.8 Timeline

- Months 1–3: pilot, seed corpus, refactoring engine v1.
- Months 4–6: Dataset A generation, baseline B1/B2 wiring.
- Months 7–9: B3 execution, analysis, paper submission.

### 4.9 Risks specific to P1

- **Refactoring engine effort creep**: if automated refactorings blow past Month 3, fall back to scripted AST rewrites plus hand-authored cases, and shrink the catalog to five classes.
- **Seed corpus too toy**: if Dafny tutorials dominate, add `IronFleet` modules as a seeded "realistic" stratum and report stratified metrics.

---

## 5. Project P2 — Structured symbolic repair for Dafny proofs

### 5.1 Claim

Alignment across related versions, combined with a small calculus of repair operators, restores more broken proofs than syntactic transfer and does so with substantially fewer verifier calls than LLM-only repair.

### 5.2 Research questions

- **RQ2.1** Which alignment signals (AST, CFG, named entity, locality) are sufficient to map proof-relevant artifacts across semantics-preserving edits?
- **RQ2.2** Which repair operators contribute most to restoration — assertion reinsertion, invariant strengthening, lemma rebinding, trigger reshaping, or intermediate-fact insertion?
- **RQ2.3** Under matched wall-clock and matched candidate budgets, does symbolic repair outperform B2 and B3 from P1?

### 5.3 Scope

- **Alignment engine**: aligns functions, loops, assertions, contracts, helper lemmas. Deliberately avoids full VC-to-VC alignment.
- **Repair operators v1** (five operators, as in the original revised plan §4.3).
- **Search**: best-first over operator × site, ranked by locality and verifier feedback.
- Evaluated on **Dataset A** from P1.

### 5.4 Baselines

- **B1, B2, B3** from P1 (re-run under matched budget).
- **B4 Symbolic-only ablation** = full P2 system, no LLM. This is the main "ours" in P2.
- **B5 Operator ablations**: remove one operator at a time.

### 5.5 Metrics and success threshold

- **M2.1** Automatic repair rate (proof-checked, zero human edits).
- **M2.2** Candidate budget: median and p95 candidates tried before success/failure.
- **M2.3** Wall-clock restoration time.
- **M2.4** Alignment precision/recall on a stratified 150-pair labeled sample; two labelers, Cohen's κ ≥ 0.7 required before numbers are reported.
- **M2.5** Patch size (normalized source-level edit count).
- **Success**: B4 beats B2 by ≥ 15 percentage points absolute on M2.1, with bootstrap 95% CI excluding zero; and B4 reaches comparable M2.1 to B3 at ≤ 30% of B3's median candidate count.

### 5.6 Deliverables

1. Repair system (open source).
2. Alignment labeling protocol and labeled subset.
3. FM/PL paper with ablation-driven evidence for each operator.

### 5.7 Target venues

- Primary: **VMCAI**, **NFM**, **iFM**, **SEFM**, **FormaliSE**, **TAP**.
- Secondary: **FMCAD** (tool), **APLAS**, **TASE**.

### 5.8 Timeline

- Months 7–10: alignment engine (starts overlapping with P1's tail).
- Months 11–13: repair operators v1, symbolic-only prototype, matched-budget evaluation.
- Months 14–16: ablations, alignment-accuracy labeling, paper submission.

### 5.9 Risks specific to P2

- **Alignment weaker than expected**: narrow to rename + helper-extraction refactorings and emphasize those strata; this still supports a focused paper.
- **Dafny/Boogie tooling slower than expected**: drop trigger reshaping operator first (it depends on backend introspection).

---

## 6. Project P3 — Hybrid LLM-symbolic repair with brittleness/drift triage

### 6.1 Claim

A narrow LLM candidate generator placed downstream of symbolic alignment closes the residual gap over symbolic-only repair, and a lightweight classifier reliably distinguishes repairable brittleness from genuine semantic drift well enough to avoid unsound "repair around the bug" behavior.

### 6.2 Research questions

- **RQ3.1** Does LLM candidate generation, conditioned on alignment output and verifier feedback, improve repair rate over B4?
- **RQ3.2** Can a small classifier trained on Dataset A and a labeled real-history subset (Dataset B) separate brittleness from drift at useful precision?
- **RQ3.3** Do the system's results on Dataset A transfer to real history (Dataset B)?

### 6.3 Scope

- **Narrow LLM integration**: LLM is only asked for candidate repairs *at aligned sites*, with operator type constraints. No free-form patch generation.
- **Dataset B**: 50–120 mined pairs from Dafny GitHub history (or the Month-1 fallback ecosystem); pairs must have verifying old versions and reproducible breakage.
- **Dataset C**: 60–100 drift/brittleness cases, double-labeled by the researcher and one external labeler (named in advance), κ target 0.7, unresolved cases excluded from quantitative claims.
- **Classifier**: features from alignment output, error-message structure, and edit signature; simple model (logistic regression or gradient-boosted trees) to keep interpretability.

### 6.4 Baselines

- **B3** LLM-only (from P1).
- **B4** Symbolic-only (from P2).
- **Ours-P3** = B4 + narrow LLM + triage gate.

### 6.5 Metrics and success threshold

- **M3.1** End-to-end repair rate vs B4 and B3.
- **M3.2** Classifier precision, recall, F1 on Dataset C.
- **M3.3** Transfer: repair rate on Dataset B compared to Dataset A, reported as a ratio.
- **M3.4** Soundness audit: fraction of "repaired" Dataset C drift cases that the triage gate correctly escalates. Target ≥ 90%.
- **Success**: (a) Ours-P3 beats B4 by ≥ 10 percentage points on M3.1 with bootstrap 95% CI excluding zero, **or** (b) Ours-P3 matches B4's M3.1 at lower candidate cost *and* the classifier reaches F1 ≥ 0.75 on M3.2.

### 6.6 Deliverables

1. Hybrid system and triage classifier.
2. Dataset B (real-history) and Dataset C (drift labels) with labeling protocol.
3. AI4SE paper combining the integration result and the triage study.

### 6.7 Target venues

- Primary: **ASE** (short/tool), **MSR**, **ISSTA** (short), **ICSME** (tool), **SANER** (short).
- Secondary workshops: **LLM4Code**, **AIware**, **NLBSE**.

### 6.8 Timeline

- Months 15–17: Dataset B mining, Dataset C labeling protocol, external labeler onboarded.
- Months 18–20: narrow LLM integration, classifier training, triage gate.
- Months 21–22: transfer evaluation, paper submission.

### 6.9 Risks specific to P3

- **LLM adds little**: acceptable outcome; paper reframes around the triage classifier alone, which is still a complete contribution.
- **Real-history corpus too small**: expand to `dafny-lang` ecosystem plus one adjacent Boogie-based verifier if Month-15 mining yields < 50 pairs.
- **Labeling disagreement**: shrink Dataset C to high-agreement cases and present it as bounded decision support.

---

## 7. Publishability fallback matrix

| Scenario | What is still publishable |
| -------- | ------------------------- |
| P1 lands, P2 stalls | P1 at empirical SE venue; thesis becomes an empirical thesis with P2 as preliminary system. |
| P1 + P2 land, P3 stalls | Full thesis stands; P3 becomes a future-work chapter. |
| All three land | Thesis has three papers; integration chapter frames them as a maintenance pipeline. |
| P2 lands but P1 paper rejected | P1 data is still the evaluation substrate for P2; reshape P1 into a benchmark release paper (MSR data track). |

---

## 8. Month-1 de-risking pilot (gate before full commitment)

Before Month 2, execute a one-month pilot to validate Dafny as the ecosystem:

- Can we find ≥ 120 candidate real-history pairs (for P3 Dataset B) where the old version verifies and a breakage can be reproduced?
- Can we script three of the seven refactorings (rename, helper extraction, ghost-code movement) end-to-end on 20 seed programs?
- Is per-program verification time tractable (< 5 min median) on chosen hardware?

**Gate rule**: if any of the three fails, switch ecosystem to Verus before committing to the P1 engine.

---

## 9. Consolidated timeline

| Months | P1                                     | P2                       | P3                            |
| ------ | -------------------------------------- | ------------------------ | ----------------------------- |
| 1      | Pilot / gate                           | —                        | —                             |
| 2–3    | Seed corpus, engine v1                 | —                        | —                             |
| 4–6    | Dataset A, B1/B2                       | —                        | —                             |
| 7–9    | B3, paper, submit                      | Alignment engine         | —                             |
| 10–13  | (revisions)                            | Operators, prototype     | —                             |
| 14–16  | —                                      | Ablations, paper, submit | —                             |
| 15–17  | —                                      | (revisions)              | Dataset B, Dataset C labeling |
| 18–20  | —                                      | —                        | LLM integration, classifier   |
| 21–22  | —                                      | —                        | Transfer eval, paper, submit  |
| 23–24  | Thesis write-up and artifact packaging | (as above)               | (as above)                    |

Slack is concentrated in Months 10–13 and 15–17 to absorb paper revision cycles.

---

## 10. Thesis integration

The thesis document is organized as:

1. **Part I — Problem and characterization** (from P1): motivation, refactoring catalog, empirical brittleness study, failure-mode taxonomy.
2. **Part II — Structured repair** (from P2): alignment, operator calculus, symbolic-only evaluation, ablations.
3. **Part III — Triage and integration** (from P3): LLM integration, drift classifier, real-history transfer.
4. **Part IV — Synthesis**: unified pipeline, negative results, limits of generality, future work.

Each part corresponds to one submitted paper. The thesis contribution is the *composition* — a repair pipeline that is empirically grounded, technically structured, and operationally safe.

---

## 11. Positioning

> This work does not solve proof maintenance in all verification ecosystems. It shows, in one realistic verifier setting and through three complementary studies, that proof repair over related versions is a practical and empirically superior alternative to treating every breakage as a fresh proving problem.

Each of the three studies is publishable on its own at a CORE rank B venue. Together they form a thesis with a single coherent claim and four concrete artifacts: a refactoring-induced breakage benchmark, a structured repair system, a hybrid/triage extension, and a labeled real-history corpus.
