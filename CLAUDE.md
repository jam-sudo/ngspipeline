# NGSpipeline

Perturb-seq raw-read pipeline: FASTQ → GEX/guide count matrices → per-cell guide assignment → ALIVE-ready h5ad.
Nextflow DSL2, nf-core conventions. Downstream consumer: ALIVE ([https://github.com/jam-sudo/alive](https://github.com/jam-sudo/alive)).

Document roles — read in this order:

- `CLAUDE.md` (this file): how the agent behaves. Stable.
- `PLAN.md`: task definitions and Definitions of Done. Static spec; changes only when a task definition changes.
- `docs/progress.md`: what is done, with evidence. The only status document.
- `docs/decisions/`: one file per decision; `docs/decisions/README.md` is the index.
- `docs/learning_debt.md`: unanswered explanation checks.
  Nothing is "done" until the human has run the DoD commands and recorded the result in `docs/progress.md`.

## Current state

<!-- Kept by the agent since 2026-09-16 under the human's delegation. Keep to pointers; details live in docs/progress.md. -->

- Active task: T-13b done; next T-40 (README completion) after human-executed T-03/T-05/T-30/T-31; Phase 5 needs learning debt cleared
- Pipeline name: ngspipeline — docs/decisions/004-naming.md
- Dev host: MacBook + colima (Rosetta; Apptainer in the VM for singularity) — docs/decisions/003-dev-host.md (accepted)
- Dataset: Replogle 2022 K562 essential lane_4 — docs/decisions/001-dataset.md (accepted); chemistry 10XV3 confirmed
- Quantifier: kallisto|bustools, prebuilt cDNA index for the full reference — docs/decisions/002-quantifier.md (accepted)
- Last green CI: https://github.com/jam-sudo/ngspipeline/actions/runs/35049830245 (T-20, all 13 checks); dev now contains PRs #2–#18
- Open learning debt: none recorded; 45 explanation-check questions (3 per PR #2–#16) await the human's answers before Phase 5 (docs/learning_debt.md)

## Rules

1. Never guess accessions, file sizes, tool versions, chemistry/whitelist names, or parameter defaults. Write `NEEDS_HUMAN: <question>` in the PR body and stop that thread of work.
2. Never weaken a test or change an expected value to make it pass. Any expected-value change requires a `docs/decisions/` entry and explicit human approval in the PR.
3. `nextflow run . -profile test,docker` must finish in &lt; 5 min on the dev host. Meet this by shrinking test data, never by bypassing pipeline stages.
4. Reuse nf-core modules (`nf-core modules install <tool>`). Hand-written modules are limited to `modules/local/{guide_index,guide_count,guide_assign,to_alive_h5ad}`. If you believe a fifth is required, write `NEEDS_HUMAN:` with the reason.
5. Every output must be reproducible by `nextflow run`. No result files produced outside the pipeline are committed.
6. Discordance with published guide assignments is a finding to document in `docs/01_guide_assignment_validation.md`, never a target to tune away. Do not adjust thresholds to raise concordance.
7. One task per session and per PR. Commit messages start with the task id (`T-12: ...`). PR body must contain: the DoD commands exactly as run, their output, and 3 explanation-check questions.
8. Do not start a task whose prerequisites in PLAN.md are not marked done in `docs/progress.md`.
9. Do not run anything that costs money (AWS) — configure only; the human executes Phase 4 runs.
10. Prefer editing `docs/decisions/` drafts over making silent choices. A choice that isn't in a decision record doesn't exist.
11. ALIVE is out of scope: never edit ALIVE code, never read or write its RPE1 sealed holdout. If ALIVE's loader cannot consume the h5ad without changes, write docs/decisions/007-alive-loader-gap.md and mark T-14 blocked (PLAN.md T-14 "ALIVE 경계").

## Commands

- Lint: `nf-core pipelines lint`
- Test: `nextflow run . -profile test,docker -resume`
- Unit: `nf-test test tests/`
- Schema: `nf-core pipelines schema build`
- Full: `nextflow run . -profile <local|slurm|awsbatch>,<docker|singularity> --input samplesheet.csv --guides guide_library.csv --outdir results`

## Layout

```
main.nf  nextflow.config  nextflow_schema.json
conf/{base,test,local,slurm,awsbatch}.config
modules/nf-core/            # installed, never edited by hand
modules/local/{guide_index,guide_count,guide_assign,to_alive_h5ad}/
subworkflows/local/{gex_quant,guide_quant}/
workflows/alive_upstream.nf
bin/guide_assign.py  bin/to_alive_h5ad.py
assets/{test_data/,guide_library_test.csv,samplesheet_test.csv,multiqc_config.yml}
tests/                      # nf-test
docs/decisions/{README.md,NNN-<topic>.md}   docs/progress.md   docs/learning_debt.md
docs/learning/                  # human's Phase 1 notes (T-05)
docs/01_guide_assignment_validation.md   docs/02_resume_check.md   docs/03_cross_profile_hashes.md
```

## Decision records

`docs/decisions/NNN-<topic>.md` — Context / Options / Choice / Consequences. Agent drafts, human approves by adding `Status: accepted` and a date.
