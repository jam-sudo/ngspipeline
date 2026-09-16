# 02 — `-resume` check

Status: verified 2026-09-15 (T-21). Procedure: `bin/resume_check.sh <outdir>` runs `-profile test,docker`, sends SIGTERM to Nextflow as soon as `KALLISTOBUSTOOLS_COUNT` is submitted, then re-runs with `-resume` and tabulates the second trace: tasks marked `CACHED` were reused, tasks marked `COMPLETED` were re-executed.

Expected shape (to be replaced by the actual traces): FASTQC ×2, KALLISTOBUSTOOLS_REF and GUIDE_INDEX (completed before the kill) → `CACHED`; KALLISTOBUSTOOLS_COUNT (killed) and everything downstream (GUIDE_COUNT if not yet finished, GUIDE_ASSIGN, TO_ALIVE_H5AD, MULTIQC) → `COMPLETED`.

## Run 1 (interrupted)

`bin/resume_check.sh ~/ngs_data/runs/resume_check` — SIGTERM sent to the Nextflow JVM 1 s after `KALLISTOBUSTOOLS_COUNT` appeared in the log; GUIDE_COUNT was running at the same moment.

| process                                           | status      | realtime |
| ------------------------------------------------- | ----------- | -------- |
| GUIDE_INDEX (guide_library_test)                  | `COMPLETED` | 8s       |
| KALLISTOBUSTOOLS_REF (mini_genome.fa)             | `COMPLETED` | 16s      |
| FASTQC (replogle_k562_lane4_test_gex)             | `COMPLETED` | 7s       |
| FASTQC (replogle_k562_lane4_test_guide)           | `COMPLETED` | 4s       |
| GUIDE_COUNT (replogle_k562_lane4_test)            | `ABORTED`   | -        |
| KALLISTOBUSTOOLS_COUNT (replogle_k562_lane4_test) | `ABORTED`   | -        |

## Run 2 (`-resume`)

| process                                           | status      | realtime |
| ------------------------------------------------- | ----------- | -------- |
| FASTQC (replogle_k562_lane4_test_gex)             | `CACHED`    | 7s       |
| KALLISTOBUSTOOLS_REF (mini_genome.fa)             | `CACHED`    | 16s      |
| FASTQC (replogle_k562_lane4_test_guide)           | `CACHED`    | 4s       |
| GUIDE_INDEX (guide_library_test)                  | `CACHED`    | 8s       |
| KALLISTOBUSTOOLS_COUNT (replogle_k562_lane4_test) | `COMPLETED` | 41s      |
| GUIDE_COUNT (replogle_k562_lane4_test)            | `COMPLETED` | 50s      |
| GUIDE_ASSIGN (replogle_k562_lane4_test)           | `COMPLETED` | 0ms      |
| TO_ALIVE_H5AD (replogle_k562_lane4_test)          | `COMPLETED` | 2s       |
| MULTIQC (ngspipeline)                             | `COMPLETED` | 14s      |

Summary: **CACHED 4, COMPLETED 5**; pipeline completed successfully.

## Verdict

**Yes.** The four processes that had finished before the interruption (FASTQC ×2, KALLISTOBUSTOOLS_REF, GUIDE_INDEX) were `CACHED`; the two processes that were running when Nextflow was killed (KALLISTOBUSTOOLS_COUNT, GUIDE_COUNT — both `ABORTED` in run 1) and everything downstream of them (GUIDE_ASSIGN, TO_ALIVE_H5AD, MULTIQC) were re-executed. MULTIQC additionally re-runs on every `-resume` because its inputs include `collectFile` products (versions, kb_quant table) that are regenerated each run; this is expected Nextflow behaviour and costs ~15 s.

Note on the procedure: signalling only the launcher subshell does not interrupt Nextflow (the JVM finishes the run); the script therefore signals the JVM child directly and waits for the session lock to be released before the resumed run.
