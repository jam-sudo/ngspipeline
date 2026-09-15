# 002 — GEX quantifier

Status: draft (agent-proposed; human sets accepted)
Task: T-02

## Context

Candidates: kallisto|bustools (`kb-python`, nf-core `kallistobustools/{ref,count}`) vs STARsolo (nf-core `star/{genomegenerate,align}`).
PLAN.md decision rule: if a STAR human index cannot be built on any available host, kallisto|bustools is the default.

Measured facts (2026-09-15):

- MacBook has 24 GB RAM (003). A STAR human genome index needs ~32 GB RAM; the colima VM is capped at 12 GB. STAR index build is not attempted on the MacBook.
- WSL2 desktop (48 GB) is offline (003), so STAR cannot be measured there today.
- kallisto|bustools index: `kb ref --workflow standard` with Ensembl release 116 GRCh38 primary assembly + GTF, run in the nf-core module container `quay.io/biocontainers/kb-python:0.28.2--pyhdfd78af_2` under amd64 emulation. Result: PENDING_MEASUREMENT (build time, peak RSS, index size are appended below when the run finishes).

## Options

|                   | kallisto\|bustools                               | STARsolo                            |
| ----------------- | ------------------------------------------------ | ----------------------------------- |
| Method            | pseudoalignment to transcriptome                 | spliced genome alignment            |
| Index RAM (human) | a few GB                                         | ~32 GB                              |
| Output            | cells×genes count matrix (mtx/h5ad), no BAM      | count matrix + BAM                  |
| nf-core modules   | `kallistobustools/ref`, `kallistobustools/count` | `star/genomegenerate`, `star/align` |
| Guide counting    | same tool via kite workflow (T-12 option)        | separate tool needed                |
| Fit to hosts      | builds on MacBook                                | needs WSL2/HPC                      |

## Choice

Proposed: **kallisto|bustools** (kb-python 0.28.2 as pinned by the nf-core module). Reason: PLAN.md decision rule is satisfied by measured facts (no host with ≥32 GB reachable). STARsolo remains a possible Phase-4 extension if the desktop or Discovery becomes available; it is not a target.

## Consequences

- T-11 uses `modules/nf-core/kallistobustools/ref` and `count`; `--reference_index` accepts a prebuilt kb index directory (index.idx, t2g.txt).
- Empty-droplet filtering: kb count's built-in filter (`--filter bustools`) or an nf-core module; decided in T-11.
- No BAM output; if a BAM is ever required, that is a new decision record.
- Reference: Ensembl release 116 GRCh38 primary assembly + GTF (download verified against Ensembl CHECKSUMS; recorded in T-02 PR body).
