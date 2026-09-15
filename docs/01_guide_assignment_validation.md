# 01 — Guide assignment validation against the authors' identities

Status: in progress (T-16). Sample: Replogle 2022 K562 day-6 essential-scale, GEM group `lane_4` (001). Reference: prebuilt kallisto index on Ensembl 116 cDNA+ncRNA (002). Assignment: `guide_assign.py`, thresholds from `~/ngs_data/runs/assign_params.yml` (test-only values `min_umi = 5`, `min_ratio = 3`; NEEDS_HUMAN for production values — never tuned to raise concordance, CLAUDE.md rule 6).

Authors' identities: `obs[gem_group == 4]` of `K562_essential_raw_singlecell_01.h5ad` (3,681 cells, `sgID_AB`), extracted to `~/ngs_data/replogle_k562_essential_h5ad/gg4_cells.tsv`. The authors' table contains only cells that passed their guide calling (single vector, or two guides of the same gene), so "concordance" is measured on the intersection of barcodes; cells the authors dropped are invisible to this comparison.

## Run

PENDING — filled by `bin/compare_assignments.py` after the full run (`docs/01` sections: run statistics, concordance table, discordance categories, per-method comparison, causes).

## Discordance categories

| category | meaning |
| --- | --- |
| concordant | pipeline `single`, same vector as the authors |
| concordant_gene | pipeline `single`, different vector, same target gene |
| discordant_vector | pipeline `single`, different vector and gene |
| multi_pipeline_* | pipeline `multi`; sub-flag says whether the authors' vector is the top-1 or top-2 |
| unassigned_threshold | pipeline `unassigned` with the authors' vector as top-1 but top-1 UMI < `min_umi` |
| unassigned_other | pipeline `unassigned`, top-1 differs or no guide reads |
| filtered_by_pipeline | authors' cell present in the unfiltered GEX matrix but removed by the bustools cell filter |
| not_called_by_pipeline | authors' cell absent from the pipeline's GEX matrix |
| not_in_authors | pipeline cell not in the authors' table (dropped by their guide calling or QC) |
