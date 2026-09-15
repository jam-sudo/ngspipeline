#!/usr/bin/env python3
"""Merge the GEX count matrix and the per-cell guide assignment into an ALIVE-ready h5ad (T-14).

ALIVE (github.com/jam-sudo/alive, src/alive/data/replogle.py) reads `.X` as raw counts, groups
cells by exact equality of one obs column (the data card's `perturbation_key`, here `gene`)
with one control label (`non-targeting`), and aborts on NaN/blank labels. It applies no cell
QC and ignores other obs columns. Therefore (docs/decisions/006) cells whose assignment status
is not `single` are excluded from the h5ad by default and reported in `uns['assignment']`;
`--keep-nonsingle` keeps them with `gene` set to the status (`multi` / `unassigned`).

obs columns are defined in docs/alive_schema.md and must match exactly.
"""
import argparse, csv, json, sys
import numpy as np
import scipy.sparse as sp
import anndata as ad
import pandas as pd

OBS_COLUMNS = ["cell_barcode", "gene", "guide_id", "target_gene", "assignment_status", "assignment_confidence", "assignment_method",
               "top1_umi", "top2_umi", "total_guide_umi", "sample_id"]
CONTROL_LABEL = "non-targeting"


def read_mtx_csr(path, n_rows, n_cols):
    rows, cols, vals = [], [], []
    with open(path) as f:
        header = None
        for line in f:
            if line.startswith("%"):
                continue
            p = line.split()
            if header is None:
                header = tuple(int(x) for x in p[:3]); continue
            rows.append(int(p[0]) - 1); cols.append(int(p[1]) - 1); vals.append(float(p[2]))
    if header[0] != n_rows or header[1] != n_cols:
        sys.exit(f"matrix header {header} does not match {n_rows} barcodes x {n_cols} genes")
    X = sp.csr_matrix((np.asarray(vals, dtype=np.float32), (rows, cols)), shape=(n_rows, n_cols))
    X.sum_duplicates()
    return X


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--counts-dir", required=True, help="kb count output dir (uses counts_filtered/ if present, else counts_unfiltered/)")
    ap.add_argument("--assignment", required=True, help="assignment.tsv from guide_assign.py")
    ap.add_argument("--sample", required=True)
    ap.add_argument("--keep-nonsingle", action="store_true", help="keep multi/unassigned cells with gene = status (default: exclude)")
    ap.add_argument("--pipeline-version", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import os
    sub = "counts_filtered" if os.path.isdir(os.path.join(a.counts_dir, "counts_filtered")) else "counts_unfiltered"
    d = os.path.join(a.counts_dir, sub)
    barcodes = [l.strip() for l in open(os.path.join(d, "cells_x_genes.barcodes.txt"))]
    gene_ids = [l.strip() for l in open(os.path.join(d, "cells_x_genes.genes.txt"))]
    names_path = os.path.join(d, "cells_x_genes.genes.names.txt")
    gene_names = [l.strip() for l in open(names_path)] if os.path.exists(names_path) else list(gene_ids)
    X = read_mtx_csr(os.path.join(d, "cells_x_genes.mtx"), len(barcodes), len(gene_ids))

    assign = {}
    with open(a.assignment) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            assign[r["cell_barcode"]] = r
    missing = [b for b in barcodes if b not in assign]
    status_counts = {"single": 0, "multi": 0, "unassigned": 0, "no_guide_reads": 0}
    keep_idx, obs_rows = [], []
    for i, b in enumerate(barcodes):
        r = assign.get(b)
        if r is None:
            st = "no_guide_reads"; gid = ""; gene = ""; conf = np.nan; method = ""; t1 = t2 = tot = 0
        else:
            st = r["status"]; gid = r["guide_id"]; gene = r["target_gene"]; method = r["method"]
            conf = float(r["posterior"]) if r.get("posterior") not in (None, "") else (float("inf") if r["ratio"] == "inf" else float(r["ratio"]))
            t1, t2, tot = int(r["top1_umi"]), int(r["top2_umi"]), int(r["total_guide_umi"])
        status_counts[st] = status_counts.get(st, 0) + 1
        if st != "single" and not a.keep_nonsingle:
            continue
        label = gene if st == "single" else st
        if st == "single" and not label:
            sys.exit(f"cell {b} is single but has an empty target_gene")
        keep_idx.append(i)
        obs_rows.append([b, label, gid, gene, st, conf, method, t1, t2, tot, a.sample])
    if not keep_idx:
        sys.exit("no cells left after filtering")
    obs = pd.DataFrame(obs_rows, columns=OBS_COLUMNS).set_index("cell_barcode", drop=False)
    obs.index.name = None
    for c in ("gene", "guide_id", "target_gene", "assignment_status", "assignment_method", "sample_id"):
        obs[c] = obs[c].astype(str)
    obs["assignment_confidence"] = obs["assignment_confidence"].astype(np.float32)
    for c in ("top1_umi", "top2_umi", "total_guide_umi"):
        obs[c] = obs[c].astype(np.int32)
    var = pd.DataFrame({"gene_id": gene_ids, "gene_name": gene_names}, index=pd.Index(gene_ids, name=None))
    if var.index.has_duplicates:
        sys.exit("duplicate gene ids in the count matrix")
    adata = ad.AnnData(X=X[keep_idx, :], obs=obs, var=var)
    adata.uns["alive_schema"] = {"perturbation_key": "gene", "control_value": CONTROL_LABEL, "obs_columns": OBS_COLUMNS,
                                 "var_index": "gene_id (Ensembl, as in the kb t2g)", "X": "raw UMI counts, CSR float32, integer-valued"}
    adata.uns["assignment"] = {"status_counts": status_counts, "cells_in_matrix": len(barcodes), "cells_written": len(keep_idx),
                               "kept_nonsingle": bool(a.keep_nonsingle), "control_cells": int((obs["gene"] == CONTROL_LABEL).sum())}
    adata.uns["provenance"] = {"pipeline": "jam-sudo/ngspipeline", "version": a.pipeline_version, "sample": a.sample, "counts_subdir": sub}
    adata.write_h5ad(a.out)
    print(f"[to_alive_h5ad] {a.sample}: wrote {adata.n_obs} cells x {adata.n_vars} genes to {a.out}; status counts {status_counts}; "
          f"control cells {adata.uns['assignment']['control_cells']}; perturbation labels {obs['gene'].nunique()}", file=sys.stderr)


if __name__ == "__main__":
    main()
