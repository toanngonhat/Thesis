# `p1-paper`

LNCS LaTeX scaffold for **P1: Brittleness under refactoring: a Dafny benchmark and empirical study** from [../revised_plan.md](../revised_plan.md).

## Layout

- `main.tex`: paper entrypoint
- `sections/`: one logical section per file
- `figures/`: figure assets
- `tables/`: generated or hand-authored table snippets
- `notes/`: outline and submission checklist
- `llncs.cls`, `splncs04.bst`: vendored LNCS template files

## Compile

From this directory:

```bash
latexmk -pdf main.tex
```

Clean auxiliary files:

```bash
make clean
```

Clean the generated PDF and all auxiliary files:

```bash
make distclean
```

## Section Map

- `01_intro.tex`: motivation, brittleness problem, contributions
- `02_background.tex`: proof maintenance and Dafny framing
- `03_dataset_and_refactorings.tex`: Dataset A, seed corpus, seven refactoring classes, generation pipeline
- `04_baselines_and_setup.tex`: B1/B2/B3, verifier settings, cost logging, success criteria
- `05_results.tex`: breakage rate, recovery rate, cost, failure-mode taxonomy
- `06_threats_to_validity.tex`: seed bias, realism, prompt sensitivity, external validity
- `07_related_work.tex`: refactoring studies, verification maintenance, LLM/program repair
- `08_conclusion.tex`: findings and bridge to later projects
- `appendix_artifact.tex`: reproducibility and artifact packaging
- `appendix_prompt.tex`: standardized LLM prompt and retry protocol

## Notes

- Bibliography is shared with the repo root via `../references.bib`.
- Appendix inclusion is controlled by `\includeappendixtrue` in `main.tex`.
- The scaffold is submission-ready in structure, but intentionally seeded with prompts and placeholders rather than finished prose.
