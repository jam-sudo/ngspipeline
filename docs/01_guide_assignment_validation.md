# 01 — Guide assignment validation against the authors' identities

Status: results recorded 2026-09-15 (T-16); production thresholds still NEEDS_HUMAN. Sample: Replogle 2022 K562 day-6 essential-scale, GEM group `lane_4` (001). Reference: prebuilt kallisto index on Ensembl 116 cDNA+ncRNA (002). Assignment: `guide_assign.py`, thresholds from `~/ngs_data/runs/assign_params.yml` (test-only values `min_umi = 5`, `min_ratio = 3`; NEEDS_HUMAN for production values — never tuned to raise concordance, CLAUDE.md rule 6).

Authors' identities: `obs[gem_group == 4]` of `K562_essential_raw_singlecell_01.h5ad` (3,681 cells, `sgID_AB`), extracted to `~/ngs_data/replogle_k562_essential_h5ad/gg4_cells.tsv`. The authors' table contains only cells that passed their guide calling (single vector, or two guides of the same gene), so "concordance" is measured on the intersection of barcodes; cells the authors dropped are invisible to this comparison.

## Run

`nextflow run . -profile local,docker --input samplesheet_lane4.csv --guides K562_day6_essential_guide_library.csv --reference_index ~/ngs_ref/kallisto_cdna_GRCh38_ens116 --chemistry 10XV3 -params-file assign_params.yml` on the MacBook (003), started 2026-09-15 19:53 EDT, **wall 2 h 23 min** (8,567 s; `pipeline_info/execution_report_*.html`). The GEX FastQC task was killed once by the operator and retried by the nf-core `retry` strategy (1 h 32 min lost); without that the run is ≈ 50 min.

| process                                                                         | realtime    | peak RSS |
| ------------------------------------------------------------------------------- | ----------- | -------- |
| FASTQC (gex, 16 files, retry)                                                   | 20 min 48 s | 2.8 GB   |
| FASTQC (guide)                                                                  | 3 min 23 s  | 1.5 GB   |
| KALLISTOBUSTOOLS_COUNT (235,218,732 read pairs, prebuilt cDNA index, 6 threads) | 20 min 52 s | 15.9 GB  |
| GUIDE_INDEX (4,582 sgRNAs → 4,565 unique protospacers)                          | 48 s        | 329 MB   |
| GUIDE_COUNT (19,749,653 read pairs, kite:10xFB)                                 | 3 min 58 s  | 11.2 GB  |
| GUIDE_ASSIGN                                                                    | 2 s         | 485 MB   |
| TO_ALIVE_H5AD                                                                   | 25 s        | 4.2 GB   |
| MULTIQC                                                                         | 16 s        | 1.1 GB   |

Quantification: GEX 69.2 % pseudoaligned, 97.2 % of reads on the whitelist, 1,641,677 barcodes in the unfiltered matrix, **7,132 cells after the bustools filter** (85,308 genes; `expected_cells` 3,681 → 193.8 %). Guide library 68.3 % pseudoaligned; 142,490 barcodes × 4,565 features; 7,131 of the 7,132 GEX cells have guide reads.

## Results

All **3,681** authors' cells are among the pipeline's 7,132 filtered cells (0 `filtered_by_pipeline`, 0 `not_called_by_pipeline`). The pipeline calls 3,451 additional cells the authors do not list (see _Extra cells_ below).

### Method (a) threshold — `min_umi 5`, `min_ratio 3` (test-only values, not tuned)

| quantity                                    | value                                            |
| ------------------------------------------- | ------------------------------------------------ |
| authors' cells (GEM group)                  | 3681                                             |
| pipeline cells (GEX filtered)               | 7132                                             |
| common barcodes                             | 3681                                             |
| pipeline single among common                | 3557 (96.6%)                                     |
| concordant (single, same vector)            | 3532 = 96.0% of common, 99.3% of pipeline-single |
| concordant at gene level (same target gene) | 3542 (96.2% of common)                           |

| category                    | cells | % of common |
| --------------------------- | ----- | ----------- |
| concordant                  | 3532  | 96.0        |
| not_in_authors              | 3451  | 93.8        |
| multi_pipeline_top1_matches | 65    | 1.8         |
| multi_pipeline_top2_matches | 26    | 0.7         |
| unassigned_threshold        | 26    | 0.7         |
| discordant_vector           | 15    | 0.4         |
| concordant_gene             | 10    | 0.3         |
| unassigned_other            | 7     | 0.2         |

### Method (b) mixture — per-vector Poisson/Gaussian on log2 UMI; fallback `UMI ≥ 5` for vectors with < 10 non-zero cells

| quantity                                    | value                                            |
| ------------------------------------------- | ------------------------------------------------ |
| authors' cells (GEM group)                  | 3681                                             |
| pipeline cells (GEX filtered)               | 7132                                             |
| common barcodes                             | 3681                                             |
| pipeline single among common                | 3398 (92.3%)                                     |
| concordant (single, same vector)            | 3379 = 91.8% of common, 99.4% of pipeline-single |
| concordant at gene level (same target gene) | 3389 (92.1% of common)                           |

| category                    | cells | % of common |
| --------------------------- | ----- | ----------- |
| not_in_authors              | 3451  | 93.8        |
| concordant                  | 3379  | 91.8        |
| multi_pipeline_top1_matches | 148   | 4.0         |
| unassigned_other            | 75    | 2.0         |
| multi_pipeline_top2_matches | 33    | 0.9         |
| unassigned_threshold        | 26    | 0.7         |
| concordant_gene             | 10    | 0.3         |
| discordant_vector           | 9     | 0.2         |
| multi_pipeline_other        | 1     | 0.0         |

On this single GEM group most vectors have only a handful of cells (3,681 cells / 2,291 vectors ≈ 1.6), so the mixture could be fit for 125 vectors and fell back for 2,166. The authors fit per guide over the whole experiment (310,385 cells), which is not reproducible from one GEM group; the mixture path becomes meaningful only when all 48 GEM groups are processed.

Threshold and mixture give the identical (status, vector) for 3,474 / 3,681 common cells; the mixture turns 114 threshold-`single` cells into `multi` and 68 into `unassigned`, and 22 threshold-`multi` cells into `single`.

### Discordance categories (threshold), with causes

| category                    | cells | what the data show                                                                                                                                                                                                                    |
| --------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| multi_pipeline_top1_matches | 65    | authors' vector is top-1; a second vector has ≥ 1/3 of its UMIs (ratio median 1.60, max 2.94). Second vector targets a different gene in 63/65 → likely doublets or ambient guide reads that the authors' per-guide mixture tolerated |
| multi_pipeline_top2_matches | 26    | authors' vector is top-2, ratio median 1.04: two vectors with near-equal UMIs; in all 26 the top-2 vector targets the same gene as the authors' call (two vectors of one gene)                                                        |
| unassigned_threshold        | 26    | authors' vector is top-1 but has 1–4 UMIs (< `min_umi` 5): threshold boundary; the authors' mixture accepted low counts                                                                                                               |
| discordant_vector           | 15    | pipeline `single` with a different vector and gene (top-1 median 54 UMIs); the authors' vector is the top-2 in 13/15                                                                                                                  |
| concordant_gene             | 10    | same target gene, different vector (shared protospacer or two vectors of one gene)                                                                                                                                                    |
| unassigned_other            | 7     | top-1 is not the authors' vector and < 5 UMIs                                                                                                                                                                                         |

Sum of non-concordant common cells: 149 (4.0 %). No threshold was changed after seeing these numbers (CLAUDE.md rule 6).

### Extra cells (pipeline only)

3,451 cells called by the bustools knee filter are absent from the authors' table. They are not low-quality by depth: GEX UMI median 14,286 (authors' cells 13,811; authors' own `UMI_count` median 14,772 for the same cells), guide UMI median 395 vs 377. Their assignment: 1,525 `single`, 1,394 `multi`, 532 `unassigned`. The 1,394 multi and 532 unassigned are consistent with the authors removing multiplets and guide-negative cells; the 1,525 `single` cells were removed by a criterion this comparison cannot see (their processed h5ad keeps only guide-called cells and applies further QC such as `mitopercent`/`z_gemgroup_UMI`, 001). This is recorded, not resolved.

### Verdict

Concordance on the authors' cells is 96.0 % (threshold) / 91.8 % (mixture) at the vector level and 99.3 % / 99.4 % among cells the pipeline calls `single`. The 4 % residual is dominated by multi-vector cells and low-UMI cells at the `min_umi` boundary, both of which are decisions for the human (`min_umi`, `min_ratio`, 006), not tuning targets.

## Discordance categories

| category               | meaning                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| concordant             | pipeline `single`, same vector as the authors                                              |
| concordant_gene        | pipeline `single`, different vector, same target gene                                      |
| discordant_vector      | pipeline `single`, different vector and gene                                               |
| multi_pipeline_*       | pipeline `multi`; sub-flag says whether the authors' vector is the top-1 or top-2          |
| unassigned_threshold   | pipeline `unassigned` with the authors' vector as top-1 but top-1 UMI < `min_umi`          |
| unassigned_other       | pipeline `unassigned`, top-1 differs or no guide reads                                     |
| filtered_by_pipeline   | authors' cell present in the unfiltered GEX matrix but removed by the bustools cell filter |
| not_called_by_pipeline | authors' cell absent from the pipeline's GEX matrix                                        |
| not_in_authors         | pipeline cell not in the authors' table (dropped by their guide calling or QC)             |

## Appendix — the same check on 12 GEM groups (2026-09-17, Discovery run, T-14c)

Same method and thresholds as above (`min_umi 5`, `min_ratio 3`, threshold), one sample per lane, `bin/compare_lanes.sh` against the authors' `gem_group` cells. Every authors' cell of every GEM group is present in the pipeline's filtered matrix, which also confirms the lane_N ↔ gem_group N mapping for all 12. Nothing was tuned; the per-lane reports with category tables are in `docs/evidence/T-14c_concordance/`.

| lane (= gem_group) | authors' cells | pipeline cells | authors' cells found | concordant (same vector) | gene level             | multi | unassigned_threshold | unassigned_other | discordant_vector |
| ------------------ | -------------- | -------------- | -------------------- | ------------------------ | ---------------------- | ----- | -------------------- | ---------------- | ----------------- |
| 1                  | 6553           | 12391          | 6553 (100 %)         | 6271 = 95.7%             | 6295 (96.1% of common) | 135   | 98                   | 4                | 21                |
| 2                  | 6667           | 12618          | 6667 (100 %)         | 6379 = 95.7%             | 6397 (96.0% of common) | 131   | 105                  | 4                | 30                |
| 3                  | 6776           | 13151          | 6776 (100 %)         | 6488 = 95.7%             | 6503 (96.0% of common) | 142   | 100                  | 10               | 21                |
| 4                  | 3681           | 7132           | 3681 (100 %)         | 3532 = 96.0%             | 3542 (96.2% of common) | 91    | 26                   | 7                | 15                |
| 5                  | 6194           | 12090          | 6194 (100 %)         | 5948 = 96.0%             | 5967 (96.3% of common) | 137   | 59                   | 12               | 19                |
| 6                  | 7019           | 13586          | 7019 (100 %)         | 6750 = 96.2%             | 6770 (96.5% of common) | 141   | 73                   | 16               | 19                |
| 7                  | 6746           | 12875          | 6746 (100 %)         | 6453 = 95.7%             | 6471 (95.9% of common) | 122   | 114                  | 11               | 28                |
| 8                  | 7036           | 13363          | 7036 (100 %)         | 6776 = 96.3%             | 6799 (96.6% of common) | 148   | 59                   | 8                | 22                |
| 9                  | 6354           | 12565          | 6354 (100 %)         | 6059 = 95.4%             | 6080 (95.7% of common) | 132   | 99                   | 10               | 33                |
| 10                 | 6764           | 13601          | 6764 (100 %)         | 6473 = 95.7%             | 6495 (96.0% of common) | 128   | 104                  | 9                | 28                |
| 11                 | 6555           | 13012          | 6555 (100 %)         | 6292 = 96.0%             | 6316 (96.4% of common) | 122   | 72                   | 11               | 34                |
| 12                 | 5840           | 11845          | 5840 (100 %)         | 5564 = 95.3%             | 5587 (95.7% of common) | 132   | 83                   | 15               | 23                |

Concordance is 95.3–96.3 % of the authors' cells on every lane (99.1–99.4 % of the cells the pipeline calls single), i.e. the lane_4 result was not a lucky lane. The pipeline keeps about twice as many barcodes as the authors after bustools filtering; the extra cells are not in the authors' table (`not_in_authors`) and are the main reason the pooled h5ad has 104,551 single cells against the authors' 76,185 for the same GEM groups.
