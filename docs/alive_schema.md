# ALIVE h5ad schema (`alive/<sample>.h5ad`)

Produced by `bin/to_alive_h5ad.py` (`TO_ALIVE_H5AD`, T-14) from the GEX count matrix (`counts/<sample>/counts_filtered/`) and `guides/<sample>/assignment.tsv`.
Consumer: ALIVE `src/alive/data/replogle.py` (`build_index`, `ad.read_h5ad(..., backed="r")` at line 241; schema dataclass `DatasetSchema` lines 81–100; CLI `prepare` in `src/alive/cli.py` 330–397; data-card keys in ALIVE `README.md` 116–145). Read-only inspection on 2026-09-15; ALIVE code is never modified by this pipeline (CLAUDE.md rule 11).

## What ALIVE requires

| Slot                                 | ALIVE requirement (source)                                                                                                                                                                                  | What this pipeline writes                                                                                              |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `obs[perturbation_key]`              | one string/categorical column, no NaN/blank; control cells have exactly `control_value` (`replogle.py` 272–293, 403–426)                                                                                    | `obs["gene"]`, control label `non-targeting` (data card: `perturbation_key: "gene"`, `control_value: "non-targeting"`) |
| `var` index                          | non-empty unique strings when `gene_id_key` is null (`replogle.py` 298–325)                                                                                                                                 | Ensembl gene id from the kb `t2g` (data card `gene_id_key: null`); `var["gene_name"]` symbol, `var["gene_id"]` copy    |
| `.X`                                 | shape matches `var`, every value finite and ≥ 0; sparse CSR preferred; raw counts intended (`replogle.py` 331–352, 429–527; `preprocess.py` 74–99; COMPOSE writer requires integers, `fit_role.py` 605–610) | raw UMI counts, CSR `float32`, integer-valued                                                                          |
| other `obs`, `uns`, `obsm`, `layers` | ignored                                                                                                                                                                                                     | see below                                                                                                              |
| cell QC                              | none applied by ALIVE (no `mito`/`min_genes`/doublet filters in `src/alive`)                                                                                                                                | cells = bustools-filtered GEX cells with a `single` assignment (006)                                                   |
| eligibility                          | labels with `< min_cells` cells or without an external sequence are excluded by ALIVE and recorded in `index.exclusions` (`replogle.py` 374–382)                                                            | not the pipeline's concern; counts per label are in `uns["assignment"]`                                                |

## obs columns (exact, in this order)

| column                                    | dtype   | meaning                                                                                                                                            | consumed by ALIVE                 |
| ----------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `cell_barcode`                            | str     | 16-nt 10x cell barcode (also the obs index)                                                                                                        | no (index positional only)        |
| `gene`                                    | str     | perturbation label: `target_gene` of the assigned vector, or `non-targeting`; with `--keep_nonsingle`, `multi` / `unassigned` for non-single cells | **yes** (`perturbation_key`)      |
| `guide_id`                                | str     | assigned vector id (`sgID_A                                                                                                                        | sgID_B` for dual-guide libraries) | no  |
| `target_gene`                             | str     | target gene of the vector (same as `gene` for single cells)                                                                                        | no                                |
| `assignment_status`                       | str     | `single` / `multi` / `unassigned` / `no_guide_reads`                                                                                               | no                                |
| `assignment_confidence`                   | float32 | mixture posterior of the assigned vector, or top-1/top-2 UMI ratio for the threshold method (`inf` when top-2 = 0)                                 | no                                |
| `assignment_method`                       | str     | `threshold` / `mixture`                                                                                                                            | no                                |
| `top1_umi`, `top2_umi`, `total_guide_umi` | int32   | guide UMI evidence from `assignment.tsv`                                                                                                           | no                                |
| `sample_id`                               | str     | samplesheet `sample_id`                                                                                                                            | no                                |

## var

Index = Ensembl gene id **with version** exactly as kb writes it in `t2g.txt` / `cells_x_genes.genes.txt` (e.g. `ENSG00000008988.13`); columns `gene_id` (same), `gene_name` (symbol from `cells_x_genes.genes.names.txt`). ALIVE does not pin a versioning convention; if a downstream step needs unversioned ids, strip the suffix there.

## uns

`alive_schema` (perturbation key, control value, column list), `assignment` (status counts over all matrix cells, cells written, control cells), `provenance` (pipeline, version, sample, counts subdirectory).

## Data card for ALIVE

Confirmed 2026-09-16 (delegated decision): `perturbation_key = "gene"`, `control_value = "non-targeting"` — the same field name and control label as the authors' h5ad ALIVE was built on, so no ALIVE-side change is needed.

```json
{
  "h5ad": "results/alive/<sample>.h5ad",
  "perturbation_key": "gene",
  "control_value": "non-targeting",
  "gene_id_key": null,
  "counts_layer": null,
  "sequences": "<from fetch_sequences.py --id-type symbol>",
  "sequence_source": "...",
  "id_mapping_version": "..."
}
```

Checked by `bin/check_alive_schema.py <h5ad>` (T-14 DoD): obs columns and dtypes equal this table, `X` finite/non-negative/integer-valued, no blank `gene`, at least one `non-targeting` cell.
