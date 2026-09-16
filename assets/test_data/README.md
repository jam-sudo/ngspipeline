# Test data (`-profile test`)

Source: Replogle et al. 2022 (Cell; PMC9380471), K562 day-6 essential-scale Perturb-seq, GEM group **lane_4** — SRA BioProject PRJNA831566, the 12 runs listed in `runs_lane4.tsv` (8 GEX mRNA runs, 4 sgRNA runs; md5 from the ENA filereport). Cell/guide ground truth: `K562_essential_raw_singlecell_01.h5ad` (Figshare 20029387, CC BY 4.0), `obs` rows with `gem_group == 4`. Guide library: paper Table S1 (`NIHMS1812939-supplement-11.xlsx`, sheet `TabB_K562_day6_library`). Reference: Ensembl release 116 GRCh38 primary assembly + GTF. Design and rationale: `docs/decisions/008-test-data-design.md`.

## Files

| File                                              | What                                                                                                                                                                                     |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `selected_barcodes.tsv`                           | 120 authors-called cells (24 vectors × 4 + 24 non-targeting) with their feature-barcode variant and `sgID_AB` ground truth, plus 300 background barcodes (`sgID_AB`/`target_gene` = `-`) |
| `selected_genes.tsv`                              | 200 most-expressed genes in gem_group 4 (mini-genome contigs)                                                                                                                            |
| `runs_lane4.tsv`                                  | SRA runs, library type, md5                                                                                                                                                              |
| `gex_R1/R2.fastq.gz`                              | GEX reads of selected barcodes, UMI-family subsampled (cells 5%, background 100%)                                                                                                        |
| `guide_R1/R2.fastq.gz`                            | sgRNA-library reads of selected barcodes (feature-barcode variant), UMI-family subsampled (20%)                                                                                          |
| `ref/mini_genome.fa.gz`, `ref/mini_genome.gtf.gz` | one contig per selected gene (locus ± 500 bp), GTF in contig coordinates                                                                                                                 |
| `../guide_library_test.csv`                       | `guide_id,target_gene,protospacer,vector_id` for the vectors present in the cells + 6 absent vectors                                                                                     |
| `SHA256SUMS`, `STATS.txt`                         | regeneration check and extraction statistics                                                                                                                                             |

## Regenerate

```
# inputs: the 12 lane_4 FASTQs (ENA), Ensembl 116 FASTA + GTF, Table S1 pairs CSV
bin/make_test_data.sh ~/ngs_data/replogle_k562_essential_lane4 \
  ~/ngs_ref/ensembl/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz \
  ~/ngs_ref/ensembl/Homo_sapiens.GRCh38.116.gtf.gz \
  ~/ngs_data/replogle_library/K562_day6_essential_library_pairs.csv
sha256sum -c assets/test_data/SHA256SUMS
```

`selected_barcodes.tsv` / `selected_genes.tsv` were produced once by `bin/select_test_barcodes.py` from the h5ad `obs` (gem_group 4), one R1 FASTQ and the 10x 3' v3 feature-barcode translation map (kb-python/ngs_tools `10xFB`); they are committed inputs, not regenerated.

## License

Sequence reads are derived from a public SRA submission (PRJNA831566; NCBI SRA data are freely available for reuse). Cell identities and guide calls come from the authors' Figshare release under **CC BY 4.0** — cite Replogle et al. 2022, Cell 185(14):2559–2575, doi:10.1016/j.cell.2022.05.013. Reference sequence and annotation are Ensembl (unrestricted, cite Ensembl 116). This subsample is redistributed here for pipeline testing only.
