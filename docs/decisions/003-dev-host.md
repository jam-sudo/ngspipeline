# 003 — Development host

Status: draft (agent-proposed; human sets accepted)
Task: T-02

## Context

Candidates: MacBook (`~/NGSpipeline`) vs desktop WSL2 (48 GB, Tailscale SSH host `wsl`, 100.99.95.91).
Decision rule (PLAN.md T-02): if amd64 container emulation on the MacBook cannot meet the 5-min test-profile limit, develop on WSL2 and use the MacBook for edits/commits only.

Measured on 2026-09-15 (T-00/T-02):

| Item                            | MacBook                                                                                        | WSL2 desktop                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Hardware                        | Apple M5 Pro, 24 GB RAM, arm64, 667 GB free                                                    | 48 GB RAM (from PLAN; not re-measured)                                                              |
| Reachability                    | local                                                                                          | Tailscale shows host `jam-1` (100.99.95.91) offline, last seen 124 days ago; SSH not possible today |
| Container runtime               | colima 0.10.3 (vz + Rosetta), Docker CLI 29.8.0, engine 29.5.2; VM 8 CPU / 12 GB / 120 GB disk | not measured                                                                                        |
| amd64 emulation                 | `docker run --platform linux/amd64 alpine uname -m` → `x86_64` (Rosetta)                       | n/a                                                                                                 |
| Template `-profile test,docker` | **137 s wall** (FASTQC ×3 ≈ 15 s each, MULTIQC 1m29s; amd64 biocontainers under Rosetta)       | not measured                                                                                        |
| Toolchain                       | Nextflow 26.04.6, nf-core 4.1.0, nf-test 0.9.5, OpenJDK 26.0.2.1                               | not measured                                                                                        |

Colima notes: VM memory was raised from 12 GB to 20 GB for the index-build measurements (002); for day-to-day development 8 CPU / 14 GB leaves room for macOS on a 24 GB machine. Only `$HOME` and `/tmp/colima` are mounted in the VM, so the Nextflow work dir must live under `$HOME` (a run with work dir under `/private/tmp` failed with `.command.run: No such file or directory`). `~/NGSpipeline/work` is gitignored and used.

Addendum 2026-09-15 (T-23): Apptainer 1.5.3 (apptainer PPA, arm64), OpenJDK 21 and Nextflow 26.04.6 were installed _inside_ the colima VM (`colima ssh`, `~/bin/nextflow`); `-profile test,singularity` runs there in 2 min 31 s with amd64 SIF images executed through the Rosetta binfmt handler. This is the Singularity location for F3 on this host. The VM was found stopped once during the day; `colima status` is part of the session start.

## Options

1. MacBook only (colima, Rosetta amd64 emulation).
2. WSL2 desktop as dev host, MacBook for edits.
3. MacBook for development and test profile; WSL2 (when online) or cloud for full-sample runs.

## Choice

Proposed: **Option 1 for Phases 2–3** (the T-11 test profile takes 72 s under Rosetta, well under 5 min; all biocontainers used so far run under Rosetta). Full-sample Phase 4 runs are `local` on the MacBook if memory allows (kallisto index build measured in 002), else WSL2/AWS.
WSL2 is unreachable at decision time, so it cannot be the default dev host.

## Consequences

- `conf/test.config` resource caps sized to the colima VM (8 CPU / 12 GB).
- Docker Desktop is not used; the human should keep `colima start --vz-rosetta` in their session start routine (or the agent starts it) and check that `colima start` does not print `Unable to enable Rosetta`.
- In-pipeline reference building for the full human genome is not possible on this host (002); full runs use `--reference_index`.
- If WSL2 comes back online, re-measure the test profile there and update this record; the MacBook stays the primary editor.
