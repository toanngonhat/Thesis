# `data1` Literature Selection for P1

This folder supports the rewrite of `p1-paper/sections/07_related_work.tex` for **P1: Brittleness under refactoring: a Dafny benchmark and empirical study**.

## Selection rules

- Prioritize work that helps position P1 as an empirical benchmark-and-characterization paper.
- Keep the literature centered on:
  - refactoring and software evolution,
  - proof maintenance and proof refactoring,
  - Dafny-specific verification engineering,
  - proof synthesis / proof automation used as comparison points,
  - APR / LLM repair framing relevant to P1 baselines.
- Exclude general PL/FM infrastructure papers unless they directly help explain the gap P1 fills.
- Prefer primary sources and downloadable PDFs, but keep important inaccessible papers if they materially improve the positioning argument.

## Final set

### Local-core papers reused from `data/`

1. `Mens2004RefactoringSurvey`
2. `Kim2012RefactoringInTheWild`
3. `Tsantalis2014RefactoringOperations`
4. `Zaidman2010CoEvolutionProductionTest`
5. `Gazzola2017AutomaticSoftwareRepair`
6. `First2020TacTok`
7. `SanchezStern2023Passport`
8. `Feng2020CodeBERT`
9. `Guo2020GraphCodeBERT`
10. `Fried2022InCoder`
11. `Xia2023APRWithPLM`

### Online expansion

1. `Whiteside2011ProofScriptRefactoring`
2. `Whiteside2013RefactoringProofs`
3. `Adams2015Tactician`
4. `Johnsen2004TheoremReuse`
5. `Grov2016VerificationPatternsDafny`
6. `Leino2010Dafny`
7. `Leino2010VSTTEBenchmarks`
8. `Irfan2022TestingDafny`
9. `Fedchin2023ToolkitTestingDafny`
10. `DafnyBench2024`
11. `Mugnier2025ImpactVerification`
12. `Wang2026TACoDafny`
13. `Xu2026DafnyComp`
14. `Yan2025ReFormDafny`
15. `MutDafny2025`
16. `Misu2024AIAssistedDafny`

## How the set is used

- The rewritten section cites a focused subset of these papers directly.
- The rest serve as supporting evidence in `extractions.md` and as backup references if the section later expands.
- The core positioning claim is:
  - refactoring is well studied,
  - proof automation is well studied,
  - Dafny verification support and benchmarking are increasingly studied,
  - but **a reproducible Dafny benchmark for semantics-preserving refactoring and baseline recovery is still missing**.
