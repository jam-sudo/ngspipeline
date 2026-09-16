# 05 — Résumé line (T-42)

Rule (PLAN.md T-42): every claim maps to F1–F13 evidence in `docs/progress.md`; a claim without evidence is deleted, not softened.

## Line supported by today's evidence (2026-09-16)

> Built **ngspipeline**, a Nextflow DSL2 / nf-core-conventions pipeline processing Perturb-seq raw reads (FASTQ → gene and sgRNA count matrices → per-cell guide assignment → ML-ready h5ad); containerized (Docker/Singularity), CI-tested (GitHub Actions, nf-test), executed reproducibly on a laptop and a SLURM cluster (byte-identical h5ad), `-resume`-verified; guide assignment validated against the published Replogle 2022 annotations (96 % per-cell concordance without threshold tuning). Upstream of ALIVE, a perturbation-response ML project.

## Claim → evidence

| Claim                                                | Evidence                                                                                            | Status  |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------- |
| Nextflow DSL2, nf-core conventions                   | F1 lint 0 failed (`docs/evidence/T-40_F1_lint.txt`); nf-core template 4.1.0; modules from nf-core   | done    |
| FASTQ → GEX + sgRNA matrices → assignment → h5ad     | F2 test run completes all 9 processes; outputs in README "Outputs"                                  | done    |
| Containerized, Docker/Singularity                    | F2 (docker) and F3 (Apptainer) runs; same sha256 (`docs/03_cross_profile_hashes.md`)                | done    |
| CI-tested (GitHub Actions, nf-test)                  | F4 4/4 nf-test; F5 8 consecutive green PR commits (10 required)                                     | 8/10    |
| `-resume`-verified                                   | F6 `docs/02_resume_check.md`                                                                        | done    |
| Validated vs published annotations, 96 % concordance | F8 `docs/01_guide_assignment_validation.md`: 3,532/3,681 vector-level (threshold), no tuning        | done    |
| Upstream of ALIVE                                    | T-14: ALIVE's loader-side inspection reads the h5ad unchanged (`docs/alive_schema.md`); F9 baseline | partial |

## Claims removed until their evidence exists

| Removed claim                | Needs                                                                |
| ---------------------------- | -------------------------------------------------------------------- |
| "… and AWS Batch"            | T-31 (AWS Batch, human, ≤ $100) → third F7 hash                      |
| "feeds ALIVE" (baseline run) | F9: baseline on an h5ad with enough GEM groups, commit link in ALIVE |

When F9 closes, restore "Feeds ALIVE". The AWS Batch claim stays out (010).
