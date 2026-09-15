# Progress — the only status document

Update at the end of every session. `CLAUDE.md > Current state` holds pointers only; details go here.

## Task log

| Date       | Task              | Status (todo/in-progress/done/waived) | DoD evidence (command output or link)                                                                                                                                                                                                                                                                          | Learning debt                                                  |
| ---------- | ----------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 2026-09-15 | PLAN v3.1 written | done                                  | —                                                                                                                                                                                                                                                                                                              | —                                                              |
| 2026-09-15 | T-00              | done                                  | `nf-core pipelines lint`: 197 passed / 27 ignored / 36 warnings / 0 failed (PR #1 body). `git remote -v`: origin https://github.com/jam-sudo/ngspipeline.git. Actions lint job: https://github.com/jam-sudo/ngspipeline/actions/runs/35007527245 (success). PR: https://github.com/jam-sudo/ngspipeline/pull/1 | explanation check: 3 questions in PR #1, human answers pending |
| 2026-09-15 | T-01              | in-progress                           | 001 draft (PR #2) awaiting human `Status: accepted`. FASTQ: 12 lane_4 runs (24 files, 15.85 GB) in `~/ngs_data/replogle_k562_essential_lane4`, `md5sum -c` 24/24 OK against ENA `fastq_md5`. Published assignment: `K562_essential_raw_singlecell_01.h5ad` md5 OK, 310,385 rows, 3,681 in gem_group 4.         | pending (PR #2)                                                |
|            | T-02              | todo                                  |                                                                                                                                                                                                                                                                                                                |                                                                |
|            | T-03              | todo                                  |                                                                                                                                                                                                                                                                                                                |                                                                |
|            | T-05              | todo                                  |                                                                                                                                                                                                                                                                                                                |                                                                |

## Project DoD (PLAN.md §1)

| #   | Condition                         | Status | Evidence |
| --- | --------------------------------- | ------ | -------- |
| F1  | lint errors 0                     | open   |          |
| F2  | test,docker < 5 min               | open   |          |
| F3  | test,singularity                  | open   |          |
| F4  | nf-test all pass                  | open   |          |
| F5  | CI green, last 10 commits         | open   |          |
| F6  | -resume check doc                 | open   |          |
| F7  | 3 profiles, identical h5ad hash   | open   |          |
| F8  | guide assignment validation doc   | open   |          |
| F9  | ALIVE loader reads h5ad unchanged | open   |          |
| F10 | MultiQC guide section             | open   |          |
| F11 | README complete                   | open   |          |
| F12 | learning_debt.md empty            | open   |          |
| F13 | all decisions accepted            | open   |          |

## Waivers

<!-- F3/F7 slurm may be waived if Discovery account is not granted. Record reason and date. -->
