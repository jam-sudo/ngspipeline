# 001 — Dataset selection

Status: draft (agent-proposed choice; human sets accepted)
Task: T-01

## Context

Need one real Perturb-seq sample with raw FASTQ (GEX + separate guide library) and published per-cell guide assignments.
Criteria (all): total FASTQ <= 50 GB; 10x 3' or 5' standard chemistry; guide library as separate FASTQ; published per-cell assignment available; subsample redistributable.

Downstream consumer ALIVE is trained on Replogle 2022 data (its sealed holdout is RPE1; CLAUDE.md rule 11), so producing ALIVE's input from the same study's raw reads is the most meaningful demonstration. RPE1 is avoided; K562 is used.

## Options

Facts below were fetched on 2026-09-15 from ENA (PRJNA831566 filereport), Figshare (articles 20029387, 20022944), PMC9380471, GEO (GSE90546, GSE90063) and 10x dataset pages. Cells marked UNVERIFIED were not confirmed from a fetched page.

| Candidate                                          | Accession / source                                                                                                                                                       | Single-sample GEX FASTQ                                           | Guide FASTQ                                           | Chemistry                                                                                                                 | Guide FASTQ separate?                     | Published per-cell assignment                                                                                                                                                                           | License                             |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Replogle 2022, K562 essential-scale, one GEM group | SRA PRJNA831566 (7,883 runs; all NovaSeq 6000). 48 K562 essential GEM groups (`KD6_seq*_essential_mRNA_lane_N`, 8 runs each) + matching `..._sgRNA_lane_N` (4 runs each) | smallest group `lane_4`: 15.0 GB (8 runs)                         | `lane_4`: 0.84 GB (4 runs)                            | 10x 3' v3 (Gel Beads v3, CG000184 Rev C direct-capture sgRNA); whitelist 3M-february-2018 (+ feature-barcode translation) | Yes (`*_sgRNA_*` libraries per GEM group) | Guide identity in `.obs` of processed h5ad `K562_essential_raw_singlecell_01.h5ad` (10.66 GB, Figshare 20029387); guide calling code github.com/josephreplogle/guide_calling (Poisson-Gaussian mixture) | Figshare h5ad CC BY 4.0; SRA public |
| Replogle 2022, RPE1 GEM group                      | same project; smallest RPE1 group 1.04 GB GEX                                                                                                                            | 0.29-0.65 GB                                                      | 3' v3                                                 | Yes                                                                                                                       | `rpe1_raw_singlecell_01.h5ad` (8.70 GB)   | same                                                                                                                                                                                                    |
| Adamson 2016                                       | GEO GSE90546 / PRJNA354963                                                                                                                                               | SRA holds BAM only: 14.7 GB (pilot) to 183 GB (epistasis)         | separate "guide barcodes" BAMs 79-430 MB              | "10x 3' Rev A" (version not stated)                                                                                       | separate library, but BAM not FASTQ       | `GSM*_cell_identities.csv.gz` on GEO                                                                                                                                                                    | GEO public, no license text         |
| Dixit 2016                                         | GEO GSE90063 / PRJNA354362                                                                                                                                               | BAM only, 78-106 GB per run                                       | none: guide barcode is in a polyadenylated transcript | 10x 3' (version not stated)                                                                                               | No                                        | `GSM*_cbc_gbc_dict*.csv.gz` on GEO                                                                                                                                                                      | GEO public, no license text         |
| 10x "5k A549 CRISPR" (3' v3.1 dual index)          | 10xgenomics.com datasets                                                                                                                                                 | 20.2 GB tar (GEX + CRISPR combined; per-library split UNVERIFIED) | in same tar                                           | 3' v3.1 (CG000316), Capture Sequence 2; 5,867 cells                                                                       | Yes                                       | Cell Ranger `protospacer_calls_per_cell.csv` (4,867 rows)                                                                                                                                               | CC BY 4.0                           |
| 10x "1k A375 CRISPR, GEM-X 5'"                     | 10xgenomics.com datasets                                                                                                                                                 | 4.96 GB tar (combined)                                            | in same tar                                           | GEM-X 5' v3 (CG000735); 1,163 cells, 2 guides                                                                             | Yes                                       | `protospacer_calls_per_cell.csv`                                                                                                                                                                        | CC BY 4.0                           |

Rejected:

- Dixit 2016: no separate guide library (criterion fails).
- Adamson 2016: BAM-only on SRA (needs bam→fastq), chemistry version unstated so whitelist would be a guess (CLAUDE.md rule 1).
- Replogle RPE1: excluded by rule 11 (ALIVE's sealed holdout cell line), even though it is the smallest.
- 10x demos: standard and small, but the only "published assignment" is Cell Ranger's own call on the same reads; kept as fallback per PLAN.md §10 if Replogle download or guide-structure parsing fails.

## Choice

Proposed: **Replogle 2022, K562 day-6 essential-scale, GEM group `lane_4`** (mRNA 8 runs + sgRNA 4 runs, 15.9 GB total).
Published assignment source: `.obs` of `K562_essential_raw_singlecell_01.h5ad` (Figshare 20029387), filtered to this GEM group.
`--chemistry`: 10x 3' v3 (NEEDS_HUMAN to confirm from CG000184 / paper before T-11 wiring; whitelist 3M-february-2018).

### Published assignment file (downloaded 2026-09-15)

`K562_essential_raw_singlecell_01.h5ad` (Figshare file 35773219, 10.66 GB, md5 `4f1122ce1c7f13299a68df6459a266d3` verified with `md5sum -c`), stored at `~/ngs_data/replogle_k562_essential_h5ad/`.
Inspected with h5py (old anndata layout, categories under `obs/__categories`):

- 310,385 cells total; `obs` columns: `cell_barcode` (index, `<16bp>-<gem_group>`), `gem_group` (int, 48 groups = the 48 sequencing "lanes"), `gene`, `gene_id`, `sgID_AB`, `gene_transcript`, `transcript`, `UMI_count`, `core_adjusted_UMI_count`, `core_scale_factor`, `mitopercent`, `z_gemgroup_UMI`.
- `gem_group == 4` (= FASTQ `lane_4`): **3,681 cells**, 1,610 distinct `sgID_AB` values, 120 `non-targeting` cells. It is the smallest group, consistent with `lane_4` being the smallest FASTQ set.
- `sgID_AB` is a **dual-guide identity** (`GENE_+_pos.23-P1P2|GENE_-_pos.23-P1P2`): each vector carries two sgRNAs (A and B) against the same gene. 2,273 distinct values / 2,058 genes across the file. T-12/T-13 must therefore count and assign at the vector (A|B pair) level, or per sgRNA then reconcile; recorded as an input to `docs/decisions/005`.
- The h5ad contains only cells that passed the authors' guide calling; unassigned/multiplet cells are absent, so concordance in T-16 is measured on the intersection of barcodes.

## Consequences

- T-01 DoD: download 12 runs from ENA, verify `fastq_md5` from the ENA filereport, download the h5ad and record the number of cells for `lane_4`.
- Guide read structure follows 10x Feature Barcode CRISPR direct capture (Capture Sequence); T-12 must handle the sgRNA read layout, not a plain protospacer read.
- ~27 GB local disk (FASTQ + h5ad); MacBook has 667 GB free.
- If the h5ad `.obs` does not carry per-cell guide identity for this GEM group, fall back to running `guide_calling` on the authors' counts, and record that in this file.
