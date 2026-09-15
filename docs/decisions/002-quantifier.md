# 002 — GEX quantifier

Status: draft (agent-proposed; human sets accepted)
Task: T-02

## Context

Candidates: kallisto|bustools (`kb-python`, nf-core `kallistobustools/{ref,count}`) vs STARsolo (nf-core `star/{genomegenerate,align}`).
PLAN.md decision rule: if a STAR human index cannot be built on any available host, kallisto|bustools is the default.

Measured facts (2026-09-15):

- MacBook has 24 GB RAM (003). A STAR human genome index needs ~32 GB RAM; the colima VM is capped at 12 GB. STAR index build is not attempted on the MacBook.
- WSL2 desktop (48 GB) is offline (003), so STAR cannot be measured there today.
- kallisto|bustools index via the nf-core module's command (`kb ref --workflow standard`, kb-python 0.28.2 container, Ensembl 116 GRCh38 primary assembly + GTF): **OOM-killed twice**. 12 GB VM: exit 137 after 1,450 s. 20 GB VM: 24 min of "Preparing" (GTF/FASTA parsing, single-threaded), then at "Splitting genome into cDNA" RSS jumped from 3.4 GB to 20.0 GB within 20 s and the kernel killed `kb` (dmesg `Out of memory: Killed process (kb) anon-rss:20025164kB`). kb ref's genome-splitting step needs more than the 24 GB MacBook can give a VM. Ensembl files verified against Ensembl `CHECKSUMS` (FASTA `22450 861294`, GTF `49151 137815`).
- Same module command on the test mini genome (200 gene loci, 008): 16 s, 285 MB RSS — in-pipeline `KALLISTOBUSTOOLS_REF` works for small references.
- Alternative prebuilt index: `kallisto index` (kallisto bundled in the same kb-python container) on Ensembl 116 cDNA + ncRNA FASTA (`Homo_sapiens.GRCh38.cdna.all.fa.gz` `22380 179589`, `ncrna.fa.gz` `24013 40053`; 669,547 transcripts; `t2g.txt` derived from the FASTA headers `transcript<TAB>gene<TAB>gene_symbol`). Result: PENDING_MEASUREMENT (appended below).

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

- T-11 uses `modules/nf-core/kallistobustools/ref` and `count`; `--reference_index` accepts a prebuilt kb index directory (`*.idx`, `t2g.txt`). In-pipeline `kb ref` is used by the test profile (mini genome); the full-sample run (T-16) uses `--reference_index` built once by `bin/build_reference_index.sh` (kallisto index on Ensembl cDNA+ncRNA), because `kb ref` on the full genome exceeds the MacBook's memory.
- The prebuilt index and the in-pipeline index differ in transcript set (Ensembl cDNA+ncRNA FASTA vs GTF-derived); this is recorded, not hidden, and the full-run index provenance goes into `docs/03_cross_profile_hashes.md`.
- Empty-droplet filtering: kb count's built-in filter (`--filter bustools`) or an nf-core module; decided in T-11.
- No BAM output; if a BAM is ever required, that is a new decision record.
- Reference: Ensembl release 116 GRCh38 primary assembly + GTF (download verified against Ensembl CHECKSUMS; recorded in T-02 PR body).
