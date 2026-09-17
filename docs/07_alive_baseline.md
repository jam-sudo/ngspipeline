# 07 — ALIVE reads the pipeline's h5ad unchanged and runs its baseline (F9, T-14c)

Rule 11: ALIVE code is never modified; the only ALIVE-side additions are a README paragraph (jam-sudo/alive PR #18), a plumbing config and a data card. ALIVE's sealed protocols (`evaluate-once`, the RPE1 holdout) are not touched.

## What ALIVE needs and what it got

ALIVE `alive cartographer prepare --config <yaml> --data-card <json>` reads the h5ad through `src/alive/data/replogle.py::build_index` (loader unchanged), keeps perturbations with a usable protein sequence and ≥ `response_space.min_cells` cells, writes an immutable run directory, then `fit` fits the response space (library-size-10k log1p, 2,000 HVGs, 50 PCs) and the additive-ridge base predictor.

Protein sequences: `scripts/fetch_sequences.py` (ALIVE, UniProtKB release 2026_03, reviewed human entries, exactly-one rule) over the 2,057 target genes of the authors' h5ad plus the 5 library genes absent there → 1,993 usable / 5 missing / 64 ambiguous (`docs/evidence/T-14c_k562_library_sequence_provenance.json`).

## Step 1 — smoke on the single-lane h5ad (lane_4, T-16 output, sha256 305e31d1…)

Config: copy of ALIVE's `cartographer_trust_gate_k562_mini.yaml` (plumbing config) with `min_cells: 5` for this smoke only and `--mock-encoder` (numpy encoder; ESM-2 is ALIVE's real-run encoder). Sequences: the 40 most frequent lane_4 target genes (38 usable).

| stage     | result                                                                                                                                               |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prepare` | run `597b89d044c31ef5`, 1.9 s; eligible 38, excluded 1,588 (1,331 below min_cells, 257 without a sequence in the 40-gene map); splits 17 / 9 / 6 / 6 |
| `fit`     | 4.3 s; 17 base-train perturbations, 420 cells, 85,308 genes → 2,000 HVGs, PCA 50, ridge α = 100 chosen by 3-fold CV                                  |

Evidence: `docs/evidence/T-14c_alive_smoke_lane4/` (ledger, manifest summary, base predictor metadata, config snapshot, data card).

## Step 2 — pooled h5ad (12 GEM groups, `--pool_alive`, decision 011)

Pipeline run (Discovery, `sharing` partition, 2026-09-16 22:16 → 00:09 EDT): `nextflow run . -profile slurm,singularity -c sharing.config --slurm_partition sharing --slurm_account neu --input samplesheet_pool.csv --guides K562_day6_essential_guide_library.csv --reference_index kallisto_cdna_GRCh38_ens116 --chemistry 10XV3 -params-file pool_params.yml` (`min_umi 5, min_ratio 3, pool_alive: true`) — 12 samples (lanes 1–12 = GEM groups 1–12, 286 GB FASTQ, md5 264/264 OK), 75 processes, wall 1 h 52 m 8 s, 60.2 CPU h, peak RSS 36.2 GB (kb count). The lane_4 h5ad from this run has sha256 `305e31d1…`, identical to the T-16 laptop and T-30 cluster runs (third byte-identical reproduction). Evidence: `docs/evidence/T-14c_execution_trace_pool12_slurm.txt`, `T-14c_execution_timeline_pool12_slurm.html`, `T-14c_pooled.alive_summary.json`.

`alive/pooled.h5ad`: 104,551 single cells × 85,308 genes, 2,052 labels, 3,780 `non-targeting`, obs index `<barcode>-<sample_id>`, 3,389,142,067 bytes, sha256 `ce24bff91fca6907bb4c2c1955fb436e081bcb2511516ea683c81f5f584f2da2`; `bin/check_alive_schema.py` → schema OK; 456 labels with ≥ 64 cells (authors' table for the same GEM groups: 227, because the pipeline keeps about twice as many barcodes — docs/01 appendix).

ALIVE (data card `docs/evidence/T-14c_alive_pool12/data_card.json`, config = copy of ALIVE's `k562_mini` plumbing config with `min_cells: 64`, `--mock-encoder`; both committed to ALIVE in jam-sudo/alive PR #19 together with the run summary):

| stage     | result                                                                                                                                                                                                               |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prepare` | run `199f4bc77d2907b4`, 11 s; eligible 437 (excluded 1,614: 1,596 below `min_cells`, 18 without a usable sequence); splits base_train 197 / method_development 109 / conformal_calibration 66 / sealed_evaluation 65 |
| `fit`     | 86 s; 197 base-train perturbations, 24,021 cells, 85,308 genes → 2,000 HVGs, PCA 50, additive ridge α = 100 by 3-fold CV (CV error 0.5229 at α = 100 vs 0.5487 at α = 0.01)                                          |

Evidence: `docs/evidence/T-14c_alive_pool12/` (ledger, summary with eligible ids, base-predictor metadata, config snapshot, data card, prepare/fit logs). Loader diff against ALIVE `main`: none.

## What this does and does not show

- Shows: the h5ad schema in `docs/alive_schema.md` is consumed by ALIVE's real CLI path with zero loader edits (F9's first half), and a baseline fit runs on it.
- Does not show: any scientific result. The mock encoder and the plumbing config exist in ALIVE precisely for such end-to-end checks ("NOT a scientific run" in the config header). A scientific run needs ALIVE's owner approval, the ESM-2 encoder and its A100 runbook, which are ALIVE's business.
