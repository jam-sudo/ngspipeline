# 005 — Guide count method (kite vs direct match)

Status: draft (agent-proposed; human sets accepted)
Task: T-12

## Context

Guide reads (001): R2 = 30-nt TSO, then the 20-nt protospacer at a variable 0-based offset (31 in 72 %, 30 in 22 %, 32 in 6 %), then a scaffold constant that differs between guide A and guide B of a dual-guide vector. 39 % of reads have no exact 20-mer hit in a fixed window; R1 carries the feature-barcode variant of the cell barcode, which must be translated to the GEX barcode before joining. The library has 4,582 protospacers (4,565 unique: 16 sequences are shared by 2–3 guides).

PLAN.md T-12 allows two methods: kallisto|bustools **kite** (k-mer feature index with Hamming-1 variants) or **direct sequence matching** in Python (Hamming distance), whichever is simpler and sufficient.

## Options

|                                              | kite (kb-python 0.28.2)                                                                                                          | Direct matching (Python)                                            |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Offset handling                              | position-free: any 20-mer of R2 that hits the index counts                                                                       | must search a window or anchor on the scaffold                      |
| Mismatches                                   | 1 mismatch by construction (variant index); 2+ not counted                                                                       | any Hamming threshold, chosen by us                                 |
| Barcode correction / UMI dedup / translation | bustools on-list correction, UMI collapsing, `kite:10xFB` translation for 3' v3 — same machinery as GEX                          | must be re-implemented (whitelist, translation map, UMI collapsing) |
| Output                                       | cells × features Matrix Market + h5ad; same container as GEX                                                                     | custom                                                              |
| Shared protospacers                          | must be indexed once (kb refuses duplicates) → merged feature `A+B`                                                              | can attribute to both guides                                        |
| Code we own                                  | `GUIDE_INDEX` (library CSV → features.tsv → `kb ref --workflow kite`), `GUIDE_COUNT` (`kb count --workflow kite[:10xFB] --h5ad`) | a full counting tool                                                |

## Choice

Proposed: **kite**. It reuses the quantifier's own barcode/UMI/translation logic (no second implementation of whitelist handling), tolerates the variable protospacer offset without anchoring, and its output format matches the GEX matrix. Direct matching is kept only as an independent check of the kite counts on the test sample (see Result), not as a pipeline path.

Consequences of kite's design that are recorded rather than tuned away:

- Reads with ≥ 2 protospacer errors are not counted. The unmatched fraction is reported in the pipeline log and in T-16, not hidden.
- Shared protospacers are counted as one merged feature (`guideA+guideB`); `feature_map.tsv` maps merged features back to guide ids and target genes for T-13. Counts for a merged feature cannot be split between its guides.
- Counting is per sgRNA, not per vector. Dual-guide vectors are handled in T-13 (006) using `vector_id` from the library.

## Result

Test data (008): 120 cells + 300 background barcodes, 57,982 guide read pairs, 108-guide library.

- **kite** (`GUIDE_COUNT`, `kite:10xFB`): 172 barcodes × 108 features, 290 non-zero entries, 8,750 UMIs. 116/120 cells have counts.
- **Direct matching** (`bin/guide_count_direct.py`: window 28–36, exact then Hamming-1, same translation map, exact UMI collapsing): 288 (barcode, feature) pairs, 8,694 UMIs. Per read, for the 120 cells: 74 % matched (exact 16,522 + Hamming-1 901 of 23,641); against the _full_ 4,582-protospacer library 76 %, so the unmatched quarter is mostly reads with ≥ 2 errors or damaged structure, not other vectors. Background barcodes: 7 % matched (ambient reads from vectors outside the test library).
- **Agreement**: 287 pairs in both; 254/287 identical UMI counts; the rest differ by a median 2.9 % (kite slightly higher — bustools UMI handling vs. exact collapsing). 3 pairs kite-only, 1 direct-only. Per cell, the top feature agrees in 112/116 cells, and in **110/116 cells the two highest kite features are exactly the authors' vector guides (`sgID_AB`)**.
- The 4 cells without kite counts have 36–48 guide reads each in the FASTQ but no read matching any library protospacer (direct matching finds only 1–2 ambient hits); both methods agree, so this is a property of those cells' guide reads (and the 10 % UMI subsample), not of the counter.

## Consequences

- `modules/local/guide_index`, `modules/local/guide_count`, `subworkflows/local/guide_quant`. No new nf-core module needed.
- `--chemistry 10XV3` selects `kite:10xFB` (translation); `10XV2` uses `kite` (the v2 feature library shares the GEX barcodes).
- Guide matrix is left unfiltered (all barcodes); cell calling comes from the GEX matrix and the join happens in T-13/T-14.
