# Research Proposal: Refactoring-Stable Proof Repair

## Working title

**Refactoring-Stable Proof Repair: Semantic Repair for Verification under Code Evolution**

## 1. Overview

This proposal develops **Refactoring-Stable Proof Repair**, a verification-maintenance framework for repairing proofs that break after refactoring, solver upgrades, and routine code evolution. In modern verification workflows, developers rarely start from scratch: they evolve verified programs over time, reorganize code, rename abstractions, extract helper functions, strengthen interfaces, migrate libraries, and periodically update verification backends. Yet these seemingly mild changes often trigger disproportionate proof breakage. Existing tools typically treat the result as a fresh synthesis or debugging problem, forcing developers to rediscover repairs that are conceptually local and often structurally predictable.

The core idea of this project is to treat post-edit proof breakage as a **semantic repair problem over related program versions**, not as full re-verification from zero. The system will recover correspondences between old and new code, specifications, verification conditions, and proof artifacts, then use those correspondences to propose or automatically validate small repairs to assertions, invariants, triggers, lemma applications, and proof scripts. Instead of saying only "verification failed after refactoring," the tool aims to say things like:

- This proof failed because the extracted helper changed framing assumptions but preserved the original postcondition intent.
- The old lemma application still matches semantically, but now requires one additional monotonicity fact.
- This refactoring only renamed and reordered ghost-state construction; the existing proof can be repaired by re-binding two intermediate facts.
- The failure is due to solver brittleness rather than specification drift; a trigger or assertion reshaping repair is sufficient.

The project sits at the intersection of programming languages, software engineering, formal methods, and AI-assisted verification. Its value proposition is practical and timely: make verified codebases less fragile under routine maintenance, and make proof reuse a first-class engineering capability.

## 2. Problem statement

Proof breakage under software evolution remains one of the largest practical barriers to sustained verification use. Teams may successfully verify a system once, but future edits often cause maintenance costs that are far out of proportion to the semantic change made to the code.

Three forms of instability are especially common:

1. **Refactoring instability**: semantics-preserving program transformations still regenerate obligations, invalidate proof scripts, or expose backend-sensitive proof failures.
2. **Backend instability**: solver upgrades, VC generation changes, or changed triggers can break proofs even when source semantics is unchanged.
3. **Specification-adjacent drift**: code evolution may preserve the original intent of the proof while slightly shifting the shape of required annotations, helper lemmas, or intermediate facts.

In current workflows, developers often respond by manually re-debugging the proof or re-synthesizing large fragments of annotation. This is expensive because tools rarely preserve enough structure from earlier proof successes to explain what survived, what changed, and which repairs are likely to work.

The result is a recurring maintenance burden:

- previously verified modules become brittle under routine cleanup;
- proof scripts become tightly coupled to accidental code structure;
- verification tools gain a reputation for being unsuitable for evolving systems;
- users under-invest in verification because they expect future proof churn.

The project addresses this gap by designing a repair layer specialized for *related versions* of verified software.

## 3. Related work

This section positions Refactoring-Stable Proof Repair against adjacent work in software refactoring, formal verification engineering, solver-aware verification infrastructure, and AI-assisted proof or repair [@Mens2004RefactoringSurvey; @Gazzola2017AutomaticSoftwareRepair; @Astrauskas2019RustTypesVerification; @deMoura2008Z3; @First2020TacTok; @SanchezStern2023Passport]. The key distinction is that our target is *maintenance under evolution* across related program versions, rather than one-shot verification, one-shot proof synthesis, or bug repair alone [@Altoyan2022RefactoringMetamodels; @Kim2012RefactoringInTheWild; @Tsantalis2014RefactoringOperations].

### 3.1 Proof engineering, proof synthesis, and proof repair

The project draws on proof engineering work that showed how much leverage comes from reusable proof artifacts and tactic/state reuse [@First2020TacTok; @SanchezStern2023Passport]. It also complements prior automated repair work, but unlike one-shot repair, we model maintenance across related verified versions where the old proof remains a meaningful hint rather than discarded context [@Gazzola2017AutomaticSoftwareRepair; @Astrauskas2019RustTypesVerification].

### 3.2 SMT-based verification infrastructure

Automated verification depends critically on the solver and intermediate verification stack (e.g., SMT standards and ecosystems, solver implementations, and modular verifier pipelines) [@Barrett2010SMTLIB; @deMoura2008Z3; @Barnett2005Boogie]. Foundational systems in this space made modern scalable verification practical and remain essential for extracting and discharging obligations [@deMoura2008Z3; @Barnett2005Boogie; @Leroy2014CompCertSSA; @Sagiv2002ShapeAnalysis].

### 3.3 Interactive theorem proving and foundational proof engineering

A large body of PL/FM research has developed powerful verification frameworks for modular and mechanized reasoning, including systems around Rust verification, Coq-based proof engineering, separation logic frameworks, and proof-oriented language infrastructures [@Astrauskas2019RustTypesVerification; @Aeneas2022RustVerification; @Flux2023LiquidTypesRust; @Xia2019InteractionTrees; @Jung2018Iris; @Jung2020SteelCore; @Protzenko2016FStar]. Representative examples include modular verification systems, foundational verifier architectures, and reusable reasoning frameworks for interactive or semi-automated proving [@Hamza2019SystemFR; @Choi2017Kami; @Jacobs2021RustHorn; @Lopes2021LLVMFormalSemantics; @Krebbers2018MoSeL].

### 3.4 Modern systems verification and Rust

Rust verification is especially relevant because it combines strong type-system guarantees with rapidly evolving backends and proof encodings [@Astrauskas2019RustTypesVerification; @Aeneas2022RustVerification; @Flux2023LiquidTypesRust; @Jacobs2021RustHorn]. This makes it a good testbed for proving that repair works under both code evolution and toolchain churn.

### 3.5 Refactoring and semantics-preserving transformations

Classical and empirical refactoring literature establishes the breadth and frequency of structural code evolution [@Mens2004RefactoringSurvey; @Kim2012RefactoringInTheWild; @Tsantalis2014RefactoringOperations]. Prior surveys and field studies characterize common refactoring operations, decision drivers, and practical adoption (e.g., the broad taxonomy of refactoring activities, studies of refactoring in the wild, and large-scale usage analyses) [@Mens2004RefactoringSurvey; @Kim2012RefactoringInTheWild; @Tsantalis2014RefactoringOperations].

### 3.6 Automated program repair

Existing software repair surveys provide useful framing for automated repair pipelines but primarily focus on fixing program defects, not restoring broken verification arguments after semantics-preserving or near-preserving evolution [@Gazzola2017AutomaticSoftwareRepair; @Xia2023APRWithPLM]. Our proposal adapts the general repair pipeline to proof artifacts and proof obligations.

### 3.7 LLM-assisted code and proof generation

Recent AI work has significantly advanced code and proof automation, including proof synthesis from corpora, representation learning for code, and language-model-based program repair [@First2020TacTok; @SanchezStern2023Passport; @Feng2020CodeBERT; @Guo2020GraphCodeBERT; @Fried2022InCoder; @Xia2023APRWithPLM]. These approaches provide valuable candidate generation capabilities and can reduce manual effort in some settings [@First2020TacTok; @Xia2023APRWithPLM].

### 3.8 Program synthesis, equivalence, and semantic alignment

Program synthesis and equivalence work supplies useful ideas for matching old and new artifacts, especially when provenance and semantic normalization are available [@Xia2019InteractionTrees; @Feng2020CodeBERT; @Guo2020GraphCodeBERT; @Fried2022InCoder]. Our contribution is to use those ideas for repair under evolution rather than only for synthesis or equivalence checking.

### 3.9 Software evolution, mining, and empirical methodology

Software maintenance and testing work emphasizes co-evolution effects and the practical difficulty of maintaining quality artifacts over time [@Zaidman2010CoEvolutionProductionTest; @Barr2014OracleProblem]. This motivates our choice to evaluate on longitudinal histories, controlled refactorings, and backend-only variations rather than on isolated proof tasks.

### 3.10 Positioning of this proposal

Across these lines of work, there is strong progress on refactoring knowledge, verifier construction, solver infrastructure, and AI-assisted generation [@Mens2004RefactoringSurvey; @Astrauskas2019RustTypesVerification; @deMoura2008Z3; @Feng2020CodeBERT]. The missing piece is a unified, refactoring-aware, backend-aware, and proof-checked *maintenance framework* for related program versions [@Altoyan2022RefactoringMetamodels; @SanchezStern2023Passport].

Refactoring-Stable Proof Repair targets this gap by combining semantic alignment across versions and proof artifacts, a structured calculus of local repair operators, explicit handling of backend-induced brittleness, hybrid symbolic plus LLM candidate generation under formal validation, and evaluation on longitudinal maintenance tasks rather than one-shot proving.

## 4. Research goal

The goal is to design, implement, and evaluate a framework that can:

- detect when proof breakage is due to refactoring or backend sensitivity rather than deep semantic drift;
- align old and new verification artifacts across code evolution;
- synthesize small, checkable repairs to proof-relevant artifacts;
- rank repairs by plausibility and maintenance cost;
- reduce human proof-maintenance effort on evolving verified codebases.

## 5. Central hypothesis

The central hypothesis is:

> If proof maintenance is treated as semantic repair over related program versions, then a verifier can recover a substantial fraction of broken proofs automatically or semi-automatically, especially for refactorings and routine maintenance edits, while reducing human debugging effort and proof churn.

This hypothesis has three parts:

- **structural continuity exists** between many old and new proof states even when surface syntax changes;
- **repair opportunities are often local** and can be expressed as small edits to assertions, triggers, lemmas, or proof scripts;
- **proof repair is more tractable than proof synthesis from scratch** when good semantic alignment is available.

## 6. Research questions

The project can be organized around the following research questions.

### RQ1. What kinds of code evolution should count as repairable proof breakage?

Which changes are best modeled as structured repair tasks rather than full re-verification? Candidate classes include renaming, extraction, inlining, loop reshaping, helper-lemma introduction, contract refactoring, ghost-code movement, and backend-induced proof failures.

### RQ2. How should old and new proof artifacts be aligned?

What combination of AST matching, CFG matching, symbolic normalization, dependency provenance, and specification intent is sufficient to align obligations and proof steps across revisions?

### RQ3. What repair operators are most effective?

Which repair actions should the system consider first: assertion insertion, invariant strengthening, trigger adjustment, proof-script rewriting, lemma substitution, framing repair, quantifier reshaping, or goal decomposition?

### RQ4. How can the system distinguish proof brittleness from true specification drift?

When a proof breaks, how can the tool decide whether the intended property still holds and the proof is merely fragile, versus whether the program’s behavior or requirements genuinely changed?

### RQ5. How much developer effort can structured repair save?

Compared with baseline re-debugging or AI-only synthesis, does semantic repair reduce time-to-fix, human edits, and downstream churn on realistic version histories?

## 7. Novelty and contribution

The proposal makes five main contributions.

### 7.1 A semantic formulation of proof repair under evolution

The project reframes proof maintenance as a relation between old and new verified artifacts, where repair acts over semantic correspondences rather than only over failing proof text.

### 7.2 A refactoring-aware alignment layer

The system introduces alignment algorithms that track proof-relevant continuity across source refactorings, contract motion, helper extraction, and obligation regeneration.

### 7.3 A repair calculus for common proof-breakage modes

The project defines a structured set of repair operators for:

- changed assertions and postconditions;
- weakened or missing intermediate facts;
- invariant adaptation;
- trigger and quantifier repair;
- lemma replacement or relocation;
- proof-script rewiring after structural edits.

### 7.4 A hybrid repair architecture

The system combines symbolic matching and rule-based repair with LLM-generated candidates, but only accepts repairs after proof checking. This makes AI a proposal mechanism, not a source of unsoundness.

### 7.5 A longitudinal benchmark for proof maintenance

The project builds a versioned corpus of proof breakage and repair episodes across multiple verification ecosystems, turning an under-supported research problem into a reusable evaluation artifact.

## 8. Proposed system design

The proposed system consists of seven stages.

### 8.1 Version-pair ingestion

For each maintenance task, the system ingests:

- an earlier verified snapshot;
- an evolved snapshot;
- code and specification diffs;
- proof artifacts, if available;
- backend metadata such as solver version and VC generation settings.

This stage establishes the assumption that the two versions are related and that reuse should be attempted.

### 8.2 Evolution classification

The system classifies edits into proof-relevant change types such as:

- renaming and movement;
- helper extraction or inlining;
- control-flow reshaping;
- contract refactoring;
- ghost-code changes;
- backend-only or solver-only changes;
- genuine semantic behavior change.

This classification determines which repair operators and alignment heuristics should be prioritized.

### 8.3 Semantic alignment of artifacts

The tool aligns old and new artifacts at multiple levels:

- source entities such as functions, loops, and assertions;
- IR or CFG regions;
- verification conditions and subgoals;
- proof steps and supporting lemmas;
- dependency slices.

Alignment will likely use a mixture of edit distance, symbolic normalization, provenance tracking, type and contract signatures, and data/control dependence context.

### 8.4 Repair opportunity detection

Once alignments are established, the system identifies likely repair sites, for example:

- a preserved goal with changed premises;
- a moved assertion whose logical role persists;
- a formerly automatic step now blocked by a missing helper fact;
- a proof script that fails due to renamed binders or reordered destructuring;
- a solver-sensitive quantifier obligation requiring trigger adaptation.

This stage narrows repair search to plausible local patches.

### 8.5 Candidate repair generation

Candidate generation combines three sources:

- **symbolic templates** derived from the detected failure mode;
- **historical reuse** from prior repairs on similar changes;
- **LLM suggestions** conditioned on aligned old/new artifacts and verifier feedback.

Examples of candidate repairs include:

- adding one assertion before a call;
- strengthening an invariant with a preserved relation;
- replacing a lemma invocation with a corresponding evolved lemma;
- rewriting a proof-script step after helper extraction;
- changing trigger syntax or quantifier shape while preserving semantics.

### 8.6 Proof-checked validation

Every candidate repair is validated by the underlying verifier or assistant. The repair layer is therefore allowed to be heuristic and generative, but the final acceptance criterion remains formal proof checking.

### 8.7 Ranking and explanation

Repairs are ranked by:

- repair size;
- locality to the change;
- semantic alignment confidence;
- verifier success;
- estimated downstream savings.

The tool should also explain each accepted or recommended repair, for example:

- "This assertion re-establishes the non-aliasing fact formerly implied by the inlined helper."
- "The property appears unchanged; this is a backend-sensitive trigger repair."
- "The old proof step survives modulo renaming and one additional bound fact."

## 9. Formalization plan

To support publication in PL or FM venues, the proposal should include a formal core.

### 9.1 Abstract model

Let:

- `P` be the original program and `P'` the evolved one;
- `S` and `S'` be their specifications and proof artifacts;
- `V(P,S)` and `V(P',S')` be extracted verification states;
- `A` be an alignment relation over proof-relevant entities;
- `R` be a repair operator acting on `S'` or its derived proof artifacts.

Then proof repair is modeled as searching for a small `R` such that:

- `R` is justified by alignments in `A`;
- `R(P', S')` restores proof obligations or proof scripts under the new version;
- the repaired result is proof-checked by the verifier.

### 9.2 Desired properties

Potential formal properties include:

- **repair soundness**: accepted repairs preserve only verifier-checked outcomes;
- **alignment conservativeness**: preserved mappings should over-approximate semantic continuity, not hallucinate equivalence;
- **repair minimality preference**: among multiple successful repairs, smaller semantically justified changes should be preferred;
- **refactoring stability**: semantics-preserving refactorings should induce repair spaces much smaller than de novo proof synthesis.

The formal model does not need to completely capture all engineering details, but it should define what it means for a proof repair to be refactoring-stable and semantically grounded.

## 10. Methodology

Five-phase plan backed by `experimental-design.csv` (single source of truth for B1-B7, M1-M8, D1-D4).

### Phase 1. Corpus construction and brittleness taxonomy

Purpose, activities, deliverables:

- builds D1 (CompCert, Iris, Mathlib, Dafny, Verus, F*, SteelCore);
- builds D2 (Prusti, RustHorn, Aeneas, Flux);
- builds D3 (synthetic refactorings from [002, 077, 078]);
- builds D4 (Z3/CVC5/Boogie variants);
- two-labeller taxonomy validation (Cohen’s kappa).

Paper: benchmark/mining paper.

### Phase 2. Alignment engine and repair calculus

- multi-level alignment (egg [065], Interaction Trees [009]);
- repair operator catalog;
- LLM candidate interface ([090, 091, 092, 094], trust [015]);
- brittleness-vs-drift classifier.

Paper: technical report.
Deliverable: B6 (ablation system).

### Phase 3. SMT-based deep prototype

- Dafny or Verus (Boogie [087] + Z3 [086] + SMT-LIB [085]);
- full B1-B7 × (D1-SMT ∪ D3 ∪ D4) × (M1, M3, M4, M5, M6, M7, M8);
- paired bootstrap, Wilcoxon signed-rank.

Paper: SMT-ecosystem tool paper.

### Phase 4. Cross-architecture extension

- Coq + Iris/MoSeL [036, 082], CompCert-style [033, 055];
- B1-B6 × (D1-Coq ∪ D3-Coq) × (M1-M6, M7);
- cross-tool conference paper.

### Phase 5. Longitudinal replay, human study, and backend analysis

- time-cursor replay over D1;
- human study per [041] measuring M2 + trust;
- full M8 on D4;
- soundness audit (R4).

Paper: flagship submission.

## 11. Candidate implementation settings

The implementation plan uses one SMT-based verifier (Phase 3) and one proof-assistant verifier (Phase 4), giving the cross-architecture evidence needed to defend the tool-agnostic claim.

- **SMT-based setting (Phase 3).** Primary candidates: **Dafny** or **Verus**, both built on Boogie [087] and Z3 [086] over SMT-LIB [085] with decision-procedure foundations from [084]. Main repair targets: assertions, invariants, helper lemmas, and solver-facing proof encodings.
- **Assistant-backed setting (Phase 4).** Primary candidate: **Coq** with Iris [082] and MoSeL [036] as the reasoning framework, using CompCert-style codebases [033, 055] as large-scale case studies and Equations [034] plus metaprogramming [037] as supporting infrastructure. Main repair targets: proof scripts, tactic states, binder structure, and lemma transport across refactoring.

This contrast matters scientifically. If both implementations only share syntax-level mechanisms, the contribution will look tool-specific. If both benefit from the same semantic alignment ideas (Phase 2 deliverables), the project establishes a genuinely cross-architecture repair abstraction, directly mitigating R2 (repairs too verifier-specific).

## 12. Technical challenges

The proposal faces several significant challenges.

### 12.1 Distinguishing semantic drift from brittleness

Not every broken proof should be repaired. Some failures reveal that the intended property no longer holds or that the specification itself should change. The system must avoid "repairing around" a real semantic regression.

### 12.2 Unstable proof artifacts

Verification conditions, solver traces, and tactic states often lack stable identities across versions. Aligning them robustly is difficult even for small code edits.

### 12.3 Search explosion in repair space

Even local proof breakage can admit many plausible repairs. The system needs strong priors and ranking to keep search tractable.

### 12.4 Unsound AI assistance

LLMs can suggest superficially plausible but semantically irrelevant repairs. The framework must treat them strictly as candidate generators under proof checking.

### 12.5 Cross-tool generality

Proof brittleness looks different in Dafny, Verus, Coq, Lean, and Viper-like systems. The project must identify a shared core rather than overfit to one platform.

## 13. Evaluation plan

The evaluation should measure repair power, maintenance savings, and workflow realism.

### 13.1 Technical evaluation

Suggested metrics:

- proof-artifact alignment precision and recall;
- repair success rate;
- proportion of repairs recovered automatically versus interactively;
- average candidate set size before successful repair;
- proof-checking time and search overhead;
- robustness across solver versions or backend upgrades.

### 13.2 Maintenance-task evaluation

Replay realistic edit histories and compare:

- baseline re-verification without repair;
- AI-only repair suggestion;
- structured semantic repair;
- structured repair plus LLM candidate generation.

Primary metrics:

- time-to-restored-proof;
- number of human edits required;
- proof artifact churn;
- percentage of tasks fully repaired;
- percentage of tasks correctly escalated as real semantic drift.

### 13.3 Human study

Use verification users with mixed experience to perform maintenance tasks such as:

- helper extraction;
- loop refactoring;
- contract refactoring;
- renamed or relocated lemmas;
- backend or solver upgrade fallout.

Human-centered metrics:

- task completion time;
- confidence in the repair;
- trust in explanation;
- perceived usefulness of ranked repair suggestions;
- qualitative judgments about whether the tool preserved original proof intent.

### 13.4 Longitudinal replay

A particularly strong evaluation would replay revision histories from real repositories and measure:

- how often old proof artifacts remain partially reusable;
- which repair operators dominate in practice;
- how often backend changes versus source changes cause breakage;
- how much maintenance effort could have been saved.

## 14. Datasets and benchmarks

Four benchmark layers, all specified in `experimental-design.csv`.

### 14.1 D1 - Real-history corpus

~2,000-5,000 pairs mined from CompCert [033, 055], Iris [082, 036], Mathlib, Dafny, Verus, F* stdlib, SteelCore [071, 089], Equations [034]. Methodology per [050, 076, 079, 081] and [041].

### 14.2 D2 - Rust verification evolution corpus

~500-1,000 pairs from Prusti [006], RustHorn [043], Aeneas [031], Flux [032], and [046]. Targets source+toolchain co-evolution under a fast-moving Rust compiler.

### 14.3 D3 - Controlled refactoring benchmark

~1,500 synthetic pairs, taxonomy from [002, 077, 078]. Gold-standard oracle for RQ1, RQ3. All pairs repairable by construction.

### 14.4 D4 - Backend-variation benchmark

~300-800 triples: Z3 [086] 4.8/4.11/4.12 × CVC5 × SMT-LIB flags [085] × Boogie encodings [087]. Primary source for M8.

## 15. Expected outcomes

The project is expected to produce:

- a semantic model of proof repair over related program versions;
- a taxonomy of proof brittleness and repair operators;
- a hybrid symbolic-plus-LLM repair prototype;
- a versioned benchmark of proof maintenance episodes;
- empirical evidence on how much structured repair reduces proof-maintenance cost.

## 16. Risks and mitigation

### Risk 1. Alignments are too noisy

Mitigation:

- start with narrower, well-structured edit classes;
- use multi-level evidence rather than source diffs alone;
- surface uncertainty explicitly and avoid over-committing to weak mappings.

### Risk 2. Repairs are too verifier-specific

Mitigation:

- define repair operators at an abstract level first;
- implement one deep prototype and one shallower transfer implementation;
- separate tool-specific extraction from tool-agnostic repair logic.

### Risk 3. LLM suggestions add little beyond symbolic repair

Mitigation:

- evaluate symbolic-only and hybrid systems separately;
- keep LLM integration narrow and high-value, such as lemma substitution or assertion wording candidates;
- emphasize proof-checked validation rather than raw generation.

### Risk 4. Many failures are actually semantic regressions

Mitigation:

- include an explicit classification layer that can recommend escalation rather than repair;
- evaluate not only successful repairs but also successful "do not repair" decisions.

## 17. Milestones and timeline

A 24-month schedule is realistic and maps directly to the five methodology phases.

### Months 1-4 (Phase 1)

- mining infrastructure + verifier replay harness;
- D1, D2, D3, D4 releases;
- two-labeller taxonomy;
- benchmark/mining paper.

### Months 5-9 (Phase 2)

- multi-level alignment (egg [065], Interaction Trees [009]);
- repair operator catalog;
- LLM interface ([090, 091, 092, 094]) under proof-checked validation [015];
- classifier training on D1 + D3;
- B6 ready.

### Months 10-14 (Phase 3)

- SMT prototype on Dafny/Verus ([085, 086, 087]);
- B1-B7 × (D1-SMT ∪ D3 ∪ D4) × (M1, M3, M4, M5, M6, M7, M8);
- SMT tool paper.

### Months 15-19 (Phase 4)

- Coq + Iris/MoSeL [036, 082], CompCert-style [033, 055];
- B1-B6 × (D1-Coq ∪ D3-Coq) × (M1-M6, M7);
- cross-tool conference paper.

### Months 20-24 (Phase 5)

- longitudinal replay over D1 with time-cursor;
- human study per [041] measuring M2 + trust;
- full M8 on D4;
- soundness audit (R4);
- flagship submission + reproducibility artifact.

## 18. Publication strategy

A staged publication strategy aligned with the five-phase methodology:

1. After Phase 1 - benchmark/mining paper (MSR, EMSE, or ASE tool track) introducing D1-D4 and the proof-brittleness taxonomy.
2. After Phase 3 - SMT-ecosystem tool paper (ASE, FSE tool track, or NFM) presenting the repair prototype with evidence from B1-B7 × D1-SMT ∪ D3 ∪ D4.
3. After Phase 4 - cross-tool conference paper (OOPSLA or PLDI if the formal repair model is the anchor; ICSE or FSE if empirical savings dominate).
4. After Phase 5 - flagship empirical paper (ICSE/FSE) on longitudinal maintenance savings, human study, and backend-stability analysis.

## 19. Why this idea matters

Verification research has improved proving power dramatically, but proof maintenance remains one of the main reasons verified systems are difficult to evolve. Refactoring-Stable Proof Repair targets that pain point directly. It matters because:

- verified software is increasingly expected to evolve rather than remain frozen;
- industrial adoption depends on maintenance cost, not just first-proof success;
- AI-assisted verification needs stronger intermediate structure than raw failures alone;
- proof brittleness is now visible as a shared PL, FM, and SE problem.

If successful, this project would help shift verification practice from "proofs break, start over" toward "proofs evolve, repair locally." That would make long-lived verified systems substantially more realistic.

## 20. Thesis-style proposal summary

This thesis proposes Refactoring-Stable Proof Repair, a framework for repairing broken proofs under software evolution by treating maintenance as semantic repair over related program versions. Instead of re-synthesizing proof artifacts from scratch, the framework aligns old and new code, specifications, obligations, and proof steps, then generates small proof-checked repairs to assertions, invariants, triggers, lemmas, and scripts. The research combines semantic alignment, refactoring-aware analysis, repair search, and hybrid symbolic-plus-LLM candidate generation, and evaluates the resulting system on real revision histories, controlled refactorings, and backend variations. The expected outcome is a principled and practical foundation for making proof maintenance more stable, explainable, and scalable in evolving verified software.

## 21. Bibliography

The proposal uses a 9-thread bibliography keyed by the numeric paper IDs already used throughout the text. The full entries live in `references.bib`.

### 21.1 Proof engineering and proof repair

[008, 010, 029, 037, 049]

### 21.2 SMT verification infrastructure

[084, 085, 086, 087, 088, 089]

### 21.3 Interactive theorem proving and foundational proof engineering

[033, 034, 036, 040, 051, 052, 055, 056, 071, 082, 083]

### 21.4 Rust verification

[006, 031, 032, 043, 046]

### 21.5 Refactoring

[001, 002, 003, 077, 078]

### 21.6 Automated program repair

[004, 080, 095]

### 21.7 LLMs for code

[015, 090, 091, 092, 093, 094]

### 21.8 Program synthesis and alignment

[009, 048, 065]

### 21.9 Software evolution and methodology

[038, 039, 041, 050, 057, 072, 076, 079, 081]
