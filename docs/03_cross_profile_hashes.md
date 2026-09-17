# 03 — Cross-profile hashes of the final h5ad

Sample: Replogle 2022 K562 essential `lane_4` (001). Command per profile: PLAN.md §2 "Full" with `--reference_index ~/ngs_ref/kallisto_cdna_GRCh38_ens116 --chemistry 10XV3 -params-file assign_params.yml` (min_umi 5, min_ratio 3, threshold).

| profile                                | host                                                                        | h5ad sha256                                                        | run date   | notes                                                                                                         |
| -------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------- |
| local,docker                           | MacBook (003), colima + Rosetta                                             | `305e31d1fa50bdcd12d2a82cef6ebf516e92c8c7d17f69eb5a02af09312a6b45` | 2026-09-15 | T-16 run; 5,082 cells × 85,308 genes, 191,167,882 bytes                                                       |
| slurm,singularity                      | Discovery (NEU), `sharing` partition, node d3196, singularity-ce 3.10.3     | `305e31d1fa50bdcd12d2a82cef6ebf516e92c8c7d17f69eb5a02af09312a6b45` | 2026-09-16 | T-30; identical to local; 28 min 9 s wall, 2.8 CPU h — `docs/evidence/T-30_lane4_slurm.txt`                   |
| slurm,singularity (12-lane run, T-14c) | Discovery `sharing`, lane_4 as one of 12 concurrent samples, fresh work dir | `305e31d1fa50bdcd12d2a82cef6ebf516e92c8c7d17f69eb5a02af09312a6b45` | 2026-09-17 | third identical reproduction; pooled.h5ad `ce24bff9…` (docs/07)                                               |
| awsbatch,docker                        | —                                                                           | waived                                                             | 2026-09-16 | T-31 execution waived by the human (docs/decisions/010-aws-waiver.md); `conf/awsbatch.config` untested on AWS |

If hashes differ, compare `obs`, `var` and `X` numerically (PLAN.md T-31 note) with `bin/check_alive_schema.py`-style scripts and record the cause here instead of the hash.

## Test profile, cross-engine (dev tip 67c7f84, 2026-09-16)

Same 18 MB test data, same host (MacBook / colima VM), Docker vs Apptainer:

| profile                  | engine                                                                 | h5ad sha256                                                        | wall              |
| ------------------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------- |
| `test,docker`            | Docker 28 in colima                                                    | `a801cc23a85d20c3e5122f88da84dbf1dcc9886a6a44cd0330cdd6fd10816427` | 93 s              |
| `test,singularity`       | Apptainer 1.5.3 inside the colima VM                                   | `a801cc23a85d20c3e5122f88da84dbf1dcc9886a6a44cd0330cdd6fd10816427` | 155 s             |
| `test,slurm,singularity` | Discovery `sharing` partition, singularity-ce 3.10.3 (T-30 smoke test) | `a801cc23a85d20c3e5122f88da84dbf1dcc9886a6a44cd0330cdd6fd10816427` | 802 s incl. queue |

Identical bytes across two container engines and two schedulers (local executor, SLURM), so neither changes the h5ad; the full-sample F7 comparison is in the table above. Evidence: `docs/evidence/T-40_F2_*`, `docs/evidence/T-40_F3_test_singularity.txt`.
