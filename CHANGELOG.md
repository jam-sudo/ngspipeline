# jam-sudo/ngspipeline: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0 - [2026-09-17]

First release. Perturb-seq raw reads → GEX and sgRNA count matrices → per-cell guide assignment → ALIVE-ready h5ad. Every completion condition F1–F13 of `PLAN.md` is recorded with evidence in `docs/progress.md`.

### `Added`

- GEX quantification with kallisto|bustools (`kb count --filter bustools`; in-pipeline `kb ref` or a prebuilt `--reference_index`) — decision 002.
- sgRNA counting with the kb kite workflow (`kite:10xFB` feature-barcode translation for 10x 3' v3) — decision 005.
- Per-cell guide assignment (`threshold`: top-1 UMI ≥ `min_umi` and top-1/top-2 ≥ `min_ratio`; `mixture`: per-vector Poisson/Gaussian EM) with defaults from the lane_4 ambient statistics — decision 009.
- ALIVE-ready `alive/<sample>.h5ad` (single-assignment cells, `obs['gene']`, raw counts) — decisions 006, schema in `docs/alive_schema.md`; `--pool_alive` writes `alive/pooled.h5ad` across GEM groups with obs index `<barcode>-<sample_id>` — decision 011.
- MultiQC report with FastQC, kb quantification and guide-assignment sections.
- 18 MB deterministic test data subsampled from Replogle 2022 lane_4 (`-profile test` < 2 min) — decision 008; nf-test module and pipeline tests.
- Profiles `local`, `slurm` (run on NEU Discovery, `docs/06_discovery_runbook.md`), `awsbatch` (configuration only, execution waived — decision 010); Docker and Singularity/Apptainer.
- Validation against the authors' guide identities: 96.0 % per-cell concordance on lane_4 and 95.3–96.3 % on 12 GEM groups without threshold tuning (`docs/01`); `-resume` check (`docs/02`); byte-identical h5ad across engines and schedulers (`docs/03`); ALIVE `prepare` + `fit` on the pooled h5ad with zero loader changes (`docs/07`).

### `Fixed`

### `Dependencies`

kb-python 0.28.2 (kallisto 0.50.1, bustools), FastQC 0.12.1, MultiQC (nf-core module), anndata; Nextflow ≥ 25.10.4, nf-core template 4.1.0.

### `Deprecated`
