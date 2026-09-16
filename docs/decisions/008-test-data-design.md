# 008 — Test-profile data design

Status: accepted (2026-09-15) — approved by the human in the Claude Code session of 2026-09-15
Task: T-10

## Context

PLAN.md T-10 requires `assets/test_data` ≤ 20 MB, built from the selected sample by **cell-barcode** subsampling (not random reads), with a small reference, and regenerable by `bin/make_test_data.sh` with identical `sha256`.

Measured on the selected sample (001, lane_4): ~235 M GEX read pairs for 3,681 cells → ~29 k reads per cell; compressed size ≈ 63 bytes per read pair. A 15 MB GEX budget holds ≈ 240 k read pairs, i.e. **8 cells at full depth**. Cell calling and guide assignment cannot be tested on 8 cells, so depth per cell must also be reduced.

## Options

1. Few cells, full depth (≈ 8 cells): fits, but too few cells to exercise cell calling, multi/unassigned states, or MultiQC statistics.
2. Many cells, random reads: breaks UMI families (a UMI's reads are split), so deduplication and UMI counts no longer behave like real data (PLAN T-10 explanation check).
3. **Many cells, UMI-family subsampling**: for a selected barcode keep a read iff `md5(barcode+UMI)` < fraction. Every read of a kept UMI is kept; UMI counts scale by the fraction, dedup behaviour is preserved. Deterministic.
4. Prefilter reads to the selected genes (run the quantifier on the full lane first): smallest data, but the generator would depend on the pipeline's own quantifier and a full-lane run.

## Choice

Option 3, with:

- **Cells**: 120 authors-called cells from `gem_group 4` = the 24 most frequent dual-guide vectors × 4 cells + 24 non-targeting cells (`assets/test_data/selected_barcodes.tsv`, with the feature-barcode variant and the authors' `sgID_AB` as ground truth for nf-test).
- **Background**: 300 whitelisted barcodes that are not cells (20–200 reads in the first 4 M reads), kept at full depth, so cell calling has empty droplets to remove.
- **Fractions**: GEX 0.05 of UMI families per selected cell, 0.02 for background barcodes, 0.1 for the guide library. A first attempt with background at 1.0 produced 116 MB (300 background barcodes carry ~6,000 reads each over the full lane); the final settings give 18 MB.
- **Reference**: "mini genome" = one contig per gene for the 200 most-expressed genes in `gem_group 4` (`selected_genes.tsv`), locus ± 500 bp, GTF rewritten to contig coordinates. The pipeline builds its own index from it, so no stage is bypassed. Reads from other genes stay in the FASTQ and simply do not map (expected mapping rate is low and is documented, not tuned).
- **Guide library**: the 24 selected vectors + 6 vectors absent from the cells (zero columns) as `guide_id,target_gene,protospacer,vector_id`; two rows per vector (sgRNA A and B).

## Result (2026-09-15)

| Output                              | Content                                                                       | Size                        |
| ----------------------------------- | ----------------------------------------------------------------------------- | --------------------------- |
| `gex_R1/R2.fastq.gz`                | 203,728 read pairs from 235,218,732 (all 120 cells have reads)                | 2.8 + 8.6 MB                |
| `guide_R1/R2.fastq.gz`              | 57,982 read pairs from 19,749,653 (all 120 cells have guide reads)            | 0.8 + 1.1 MB                |
| `ref/mini_genome.fa.gz` / `.gtf.gz` | 200 contigs; gene/transcript/exon features only                               | 1.4 + 0.8 MB                |
| `guide_library_test.csv`            | 54 vectors (24 targeting + 24 NT present in cells + 6 absent), 108 sgRNA rows | 11 kB                       |
| total `assets/test_data`            |                                                                               | **18 MB** (`du -sk` 18,176) |

Generation takes ~140 s on the MacBook; two independent runs give identical `sha256` for all six generated files.

## Consequences

- `-profile test` cell counts are ~120 called cells with ~5% of real depth; thresholds in T-13 tests must not be tuned to this data (CLAUDE.md rule 6) — nf-test uses synthetic inputs for exact expectations.
- `vector_id` is a 4th column beyond PLAN.md §2's three; needed because the library is dual-guide (001). Recorded here; 005 decides how counts/assignment use it.
- Regeneration needs the 12 lane_4 FASTQs, the Ensembl 116 FASTA/GTF and the Table S1 pairs CSV (paths in `assets/test_data/README.md`).
- The whitelist/translation map is not needed by the generator (FB barcodes are precomputed into `selected_barcodes.tsv`).
