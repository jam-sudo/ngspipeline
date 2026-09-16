# 011 — Pooled ALIVE h5ad across GEM groups

Status: accepted (2026-09-16, delegated — the human approved the agent doing everything remaining: "모두 너가 직접해 승인")
Task: T-14b (feeds F9)

## Context

ALIVE's cartographer `prepare` reads one h5ad and keeps only perturbations with ≥ `min_cells` (64 in the K562 configs) cells. One GEM group of the Replogle K562 essential dataset (~6.5 k cells over 2,291 vectors) gives 1 such gene; the authors' `gem_group` column shows that 12 GEM groups give 227 genes and 16 give 468. The pipeline is per sample (per GEM group): 10x barcodes are unique only within a GEM group, so the lanes cannot be merged as one sample, and rule 5 requires the pooled file to come out of `nextflow run`, not from an ad-hoc concat script.

## Options

1. A fifth local module `pool_h5ad` (rule 4 forbids it without NEEDS_HUMAN).
2. Extend `TO_ALIVE_H5AD` / `bin/to_alive_h5ad.py` to accept N (sample, counts dir, assignment) triples and call it a second time (`TO_ALIVE_H5AD_POOLED`, an alias of the same module) on the collected channel when `--pool_alive true`.
3. Pool in ALIVE (out of scope, rule 11).

## Choice

Option 2. Pooled obs index = `<barcode>-<sample_id>` (the `sample_id` obs column already exists); single-sample outputs keep the bare barcode and identical `uns`, so single-sample h5ad bytes are unchanged (test-profile sha256 `a801cc23…`, lane_4 `305e31d1…`). Pooling requires an identical `var` index across samples (same reference index) and fails otherwise. `uns['assignment']['per_sample']` and `uns['provenance']['samples']` record the composition. A `<id>.alive_summary.json` sidecar (cells, labels, status counts, first obs ids) is written next to each h5ad so nf-test can assert on content without reading HDF5.

## Consequences

- New param `pool_alive` (default false); `alive/pooled.h5ad` appears only with > 1 sample. Documented in README, `docs/alive_schema.md`.
- ALIVE data card for F9 points at `alive/pooled.h5ad`; `obs['gene']` and `X` semantics are unchanged.
- `tests/default.nf.test.snap` changed only by the added sidecar entry (`replogle_k562_lane4_test.alive_summary.json`, md5 4c12ab16…); every pre-existing expected value is untouched (rule 2).
- Fixtures `tests/data/alive_synthetic/` (generator `make_synthetic.py`) and `modules/local/to_alive_h5ad/tests/` cover single, pooled and `--keep-nonsingle`.
- Per-lane concordance with the authors' `gem_group` cells is checked per sample before pooling (docs/01 gets a per-lane table when the 12-lane run is done).
