# `data1` Evidence Note for P1 Related Work

This note is the source-mapped evidence used to rewrite `p1-paper/sections/07_related_work.tex`.

## `refactoring_empirical`

### `Mens2004RefactoringSurvey`
- Studies the refactoring literature as a broad software-engineering research area, covering activities, tooling, and supported artifacts.
- Matters for P1 because it establishes that refactoring is not a niche behavior; it is a mainstream maintenance activity with long-standing research attention.
- Supports P1’s starting point that structural edits are common and worth studying systematically.
- Leaves open P1’s niche because it does not focus on verified software or proof breakage.

### `Kim2012RefactoringInTheWild`
- Empirically studies refactoring decisions in open-source projects.
- Matters for P1 because it shows refactoring behavior is contextual and driven by real maintenance needs rather than laboratory examples alone.
- Supports P1’s motivation to study program evolution instead of isolated one-shot verification tasks.

### `Tsantalis2014RefactoringOperations`
- Provides large-scale evidence on the use of refactoring operations.
- Matters for P1 because it justifies a concrete refactoring catalog rather than an arbitrary transformation list.
- Supports the claim that multiple refactoring classes deserve evaluation, not only rename or extract-method.

### Synthesis

This bucket shows that refactoring is a normal part of software maintenance and that empirical SE has already characterized its prevalence and diversity. What it does **not** provide is a benchmark or empirical account of what happens when the artifact being maintained includes verification-oriented code and proof hints. That is exactly the gap P1 exploits.

## `software_evolution_maintenance`

### `Zaidman2010CoEvolutionProductionTest`
- Studies how production code and tests co-evolve in real repositories.
- Matters for P1 because it offers a methodological precedent for studying evolving artifacts together rather than evaluating them statically.
- Supports the framing that maintenance should be analyzed longitudinally and structurally.

### `Mugnier2025ImpactVerification`
- Interviews experienced Dafny users about how auto-active verification affects large-scale development.
- Matters for P1 because it connects verification to adoption cost, developer effort, and workflow friction.
- Supports the claim that maintainability and usability are central barriers even when automation exists.
- Leaves open P1’s niche because it is a user-study view of verification practice, not a benchmark of refactoring-induced breakage.

### Synthesis

This bucket strengthens the maintenance lens behind P1. Existing software-evolution work shows that artifacts co-evolve, while recent Dafny user research shows that verification effort still shapes developer behavior. P1 builds on both ideas by asking a narrower empirical question: how brittle does verification become under semantics-preserving refactoring?

## `verification_engineering`

### `Leino2010Dafny`
- Introduces Dafny as an auto-active verifier for functional correctness.
- Matters for P1 because it anchors the verifier model: code, specifications, and proof obligations are tightly coupled in one workflow.
- Supports the choice of Dafny as a realistic setting for maintenance-oriented verification studies.

### `Grov2016VerificationPatternsDafny`
- Documents recurring verification patterns in Dafny and mechanizes them in a tactic language.
- Matters for P1 because it shows that Dafny proof guidance is patterned rather than arbitrary.
- Supports the idea that proof-relevant artifacts have enough structure to be studied systematically.
- Leaves open P1’s niche because it focuses on reusable patterns, not breakage under evolution.

### `Irfan2022TestingDafny`
- Uses randomly generated Dafny programs to test verifier and compiler soundness/precision.
- Matters for P1 because it demonstrates that Dafny itself is already a target of empirical tool-study work.
- Supports positioning P1 near verification-engineering work, but with a different question: proof brittleness rather than tool soundness.

### `Fedchin2023ToolkitTestingDafny`
- Introduces DUnit, DMock, and DTest for automated testing of Dafny programs.
- Matters for P1 because it shows a growing ecosystem of support tooling around Dafny.
- Contrasts with P1 by focusing on testing and coverage, not refactoring-induced proof churn.

### `MutDafny2025`
- Applies mutation testing to identify weak Dafny specifications.
- Matters for P1 because it shows that empirical assessment of specification quality is becoming a live Dafny topic.
- Supports the broader argument that specification robustness is measurable, but leaves open how that robustness behaves under refactoring.

### Synthesis

Work in this bucket shows that Dafny is mature enough to support toolsmithing, empirical testing, and pattern-oriented engineering. That makes it a strong substrate for P1. However, these papers do not isolate the specific phenomenon P1 targets: verification failure caused by semantics-preserving refactoring of already-verified code.

## `proof_refactoring_or_maintenance`

### `Whiteside2011ProofScriptRefactoring`
- Proposes proof-script refactorings as structured, semantics-preserving transformations over proof developments.
- Matters for P1 because it is one of the clearest prior formulations of proof maintenance as refactoring rather than re-proving.
- Supports the conceptual argument that proof artifacts themselves can be maintained systematically.

### `Whiteside2013RefactoringProofs`
- Extends the formal proof-refactoring agenda into a larger framework and catalog of transformations.
- Matters for P1 because it provides depth behind the claim that proof maintenance is a real research problem, not just anecdotal pain.
- Leaves open P1’s niche because the setting is interactive theorem proving, not SMT-backed auto-active verification.

### `Adams2015Tactician`
- Presents a tool for refactoring tactic proof scripts in HOL Light.
- Matters for P1 because it demonstrates operational support for proof refactoring in practice.
- Contrasts with P1: tool support exists for interactive proof scripts, but not for benchmarking refactoring-induced brittleness in Dafny.

### `Johnsen2004TheoremReuse`
- Explores theorem reuse via proof-term transformation.
- Matters for P1 as a related idea of carrying proof artifacts across nearby statements or contexts.
- Supports the general intuition that reuse across related proof tasks is viable.

### Synthesis

This bucket is the closest conceptual ancestor of P1. It shows that proof maintenance and proof refactoring have been studied in theorem-proving settings. The missing piece is an empirical benchmark for auto-active verification under software evolution, where the proof artifact is entangled with source code, contracts, and SMT-facing hints.

## `proof_synthesis_or_automation`

### `First2020TacTok`
- Learns to synthesize proof scripts from proof states and partial scripts.
- Matters for P1 because it is a baseline family for proof automation.
- Supports the idea that proof corpora can be exploited to automate verification work, but not specifically maintenance under evolution.

### `SanchezStern2023Passport`
- Improves automated formal verification by exploiting identifiers more effectively.
- Matters for P1 because it shows that representation choices can improve proof synthesis/automation.
- Contrasts with P1: Passport uses corpora to build automation, whereas P1 measures the maintenance problem that later systems like P2 may try to solve.

### `REFactor2024`
- Learns to extract useful new theorems from proofs for theorem proving.
- Matters for P1 only as distant adjacent work on proof restructuring and reuse.
- Supports the broader trend that proof corpora are now mined not only for synthesis but for restructuring and reuse signals.

### Synthesis

This literature demonstrates that proof automation is advancing quickly, especially when proof corpora can be exploited. P1 should not compete with these papers on method novelty. Instead, it should use them to motivate why understanding the maintenance problem matters: if proofs break under evolution, synthesis and repair systems still need a realistic evaluation substrate.

## `apr_and_llm_repair`

### `Gazzola2017AutomaticSoftwareRepair`
- Surveys automated software repair pipelines.
- Matters for P1 because it provides the closest high-level repair analogy.
- Supports the use of baseline language such as generate-and-validate, while also clarifying that proof maintenance is not the same as bug repair.

### `Xia2023APRWithPLM`
- Studies automated program repair with pretrained language models.
- Matters for P1 because it directly informs the framing of the LLM-only baseline.
- Contrasts with P1 because the oracle is usually tests, not proof re-verification over related program versions.

### `Feng2020CodeBERT`, `Guo2020GraphCodeBERT`, `Fried2022InCoder`
- Represent the main line of pretrained and generative code models that inform modern repair baselines.
- Matter for P1 because the LLM-only baseline belongs to this family of techniques.
- Support baseline framing, not P1’s primary empirical contribution.

### `Misu2024AIAssistedDafny`
- Studies prompt-based synthesis of verified Dafny methods with large language models.
- Matters for P1 because it is a direct Dafny-specific example of LLM-era verification work.
- Supports the claim that current AI work is aimed mostly at generation and synthesis, not maintenance of existing verified programs.

### Synthesis

APR and code-LLM work give P1 a natural comparison point for B3. The key positioning move is to say: these methods are valuable baselines and future beneficiaries of P1, but they do not answer the empirical question of how often proof maintenance breaks under semantics-preserving refactoring.

## `dafny_or_verification_benchmarks`

### `Leino2010VSTTEBenchmarks`
- Early evidence that Dafny can be used in benchmark-style verification exercises.
- Matters for P1 because it shows a historical precedent for evaluation through curated challenge problems.

### `DafnyBench2024`
- Introduces a large benchmark for ML-assisted formal software verification in Dafny.
- Matters for P1 because it is the strongest recent benchmark-adjacent Dafny paper.
- Contrasts with P1 because it focuses on generating enough hints/specs to verify programs, not on maintaining proofs across refactoring.

### `Wang2026TACoDafny`
- Proposes automated, contamination-free generation of Dafny benchmarks.
- Matters for P1 because it reinforces that benchmark construction is itself an active research topic in the Dafny community.
- Contrasts with P1 because benchmark generation there is task-centric, not maintenance-centric.

### `Xu2026DafnyComp`
- Introduces a benchmark for compositional formal verification in Dafny.
- Matters for P1 because it is another recent benchmark paper that focuses on multi-function reasoning difficulty.
- Contrasts with P1 because its axis of difficulty is compositional specification generation rather than evolution over time.

### `Yan2025ReFormDafny`
- Combines RL and formal-language feedback in Dafny, alongside benchmark construction.
- Matters for P1 because it shows how benchmark work and automated verification research are converging in Dafny.
- Contrasts with P1 because the emphasis is scalable formal-language training, not proof maintenance after refactoring.

### Synthesis

Recent Dafny work is rapidly building benchmarks for synthesis, compositional reasoning, and specification generation. That is good news for P1: it means the ecosystem already accepts benchmark-driven empirical work. But none of these benchmarks isolate the maintenance question P1 asks, namely how often semantics-preserving refactorings break verification and how much simple baseline recovery can restore.
