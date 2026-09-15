# 006 — Non-single cells in the ALIVE h5ad

Status: draft (agent-proposed; human sets accepted)
Task: T-14

## Context

`guide_assign` labels every GEX-called cell `single`, `multi` or `unassigned` (T-13); cells without any guide read are `no_guide_reads`. ALIVE's loader (`src/alive/data/replogle.py`) groups cells by exact equality of one obs label and **aborts on NaN or blank labels**; it has no notion of guides, multiplets or unassigned cells, and applies no cell QC (docs/alive_schema.md). The authors' h5ad (001) likewise contains only cells that passed their guide calling.

## Options

1. **Exclude** non-single cells from `alive/<sample>.h5ad`; keep them in `guides/<sample>/assignment.tsv` and report counts in `uns["assignment"]` and MultiQC.
2. Keep them with `gene = "multi"` / `"unassigned"`: ALIVE would treat these as perturbation labels (they would be excluded only if `< min_cells` or lacking a sequence) — silently wrong biology.
3. Keep them with a blank label: aborts ALIVE (`SchemaError`).

## Choice

Option 1 by default (`--keep_nonsingle false`). `--keep_nonsingle true` implements option 2 for inspection only (labels are the status strings) and is not for training.

## Consequences

- The h5ad cell count is smaller than the GEX cell count; the difference is documented per run (`uns["assignment"]["status_counts"]`, MultiQC guide section).
- Multiplets are removed only when they carry two vectors; same-vector doublets are invisible to this rule (as in the authors' data).
- T-16 concordance is computed on `assignment.tsv` (all cells), not on the h5ad.
