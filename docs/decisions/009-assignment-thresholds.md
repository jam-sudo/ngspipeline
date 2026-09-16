# 009 — Guide-assignment thresholds (`min_umi`, `min_ratio`)

Status: accepted (2026-09-16) — decided by the agent under the delegation granted by the human on 2026-09-16 ("claude.md 및 기타 결정사항들 결정 권한 위임 승인")
Task: T-13 / T-16

## Context

PLAN.md T-13 leaves the production values of `--min_umi` (minimum top-1 vector UMI) and `--min_ratio` (minimum top-1 / top-2 UMI ratio) to the human; the T-16 run and the test profile used placeholder values 5 / 3. CLAUDE.md rule 6 forbids choosing thresholds to raise concordance with the authors, so the choice below is made from the **ambient-background** and **single-vector** statistics of the full lane_4 run (`~/ngs_data/runs/lane4_local`), not from the concordance table.

Measured on lane_4 (kite guide matrix, vector-level UMIs):

| quantity                                                          | value                 |
| ----------------------------------------------------------------- | --------------------- |
| non-cell barcodes with any guide UMI                              | 135,359               |
| ambient UMI per (barcode, vector): median / p99 / p99.9           | 1 / 2 / 13            |
| ambient top-1 vector UMI per non-cell barcode: median / p95 / p99 | 1 / 3 / 6             |
| called cells (7,132): top-1 vector UMI median / p5 / p1           | 313 / 2 / 1           |
| called cells: top-2 vector UMI median / p95 / p99                 | 2 / 471 / 1,095       |
| called cells with top-2 > 0: ratio median / p10 / p5              | 27.0 / 1.30 / 1.02    |
| cells with top-1 < 3 / < 5 / < 10                                 | 415 / 564 / 752       |
| cells with ratio < 2 / < 3 / < 5                                  | 1,315 / 1,970 / 2,466 |

## Options

- `min_umi`: 3 (above ambient p99 per pair, but 1 % of empty droplets reach 6), 5 (placeholder), **10** (above the ambient top-1 p99 of 6 with margin; still ≈ 30× below the single-vector median of 313), 13 (ambient per-pair p99.9; no cleaner rationale than 10).
- `min_ratio`: 2, **3**, 5. Genuine single-vector cells sit at a median ratio of 27; ratios below 3 mean the second vector carries more than a third of the top vector's UMIs, which the T-16 discordance analysis showed to be doublets or second vectors of the same gene, not noise.

## Choice

**Defaults: `min_umi = 10`, `min_ratio = 3`** (in `nextflow.config` and the schema; users can override). Rule: `min_umi` is the smallest round number above the 99th percentile of the top-1 vector UMI in _non-cell_ barcodes (6), i.e. a cell must carry more of a vector than 99 % of empty droplets do; `min_ratio = 3` keeps the multi/single boundary where the ratio distribution separates (p10 = 1.3 vs median 27). `conf/test.config` keeps 5 / 3 because the test data subsamples guide reads to 10 %.

## Consequences

- With 10 / 3 on lane_4, 752 of 7,132 cells fall below `min_umi` (564 at 5); these are almost all cells absent from the authors' table. The T-16 concordance was computed with 5 / 3 and is left as recorded (docs/01); it is not re-run to look better or worse.
- Full-run and Phase-4 commands no longer need `-params-file` for the thresholds; `--assign_method` stays `threshold` by default, `mixture` needs many GEM groups (005/T-16).
- Any later change of these defaults requires a new decision record (CLAUDE.md rule 2/6).
