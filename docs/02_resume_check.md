# 02 — `-resume` check

Status: PENDING (T-21). Procedure: `bin/resume_check.sh <outdir>` runs `-profile test,docker`, sends SIGTERM to Nextflow as soon as `KALLISTOBUSTOOLS_COUNT` is submitted, then re-runs with `-resume` and tabulates the second trace: tasks marked `CACHED` were reused, tasks marked `COMPLETED` were re-executed.

Expected shape (to be replaced by the actual traces): FASTQC ×2, KALLISTOBUSTOOLS_REF and GUIDE_INDEX (completed before the kill) → `CACHED`; KALLISTOBUSTOOLS_COUNT (killed) and everything downstream (GUIDE_COUNT if not yet finished, GUIDE_ASSIGN, TO_ALIVE_H5AD, MULTIQC) → `COMPLETED`.

## Run 1 (interrupted)

PENDING

## Run 2 (`-resume`)

PENDING

## Verdict

PENDING — re-executed processes are exactly the interrupted one and its descendants: yes/no, with the table above as proof.
