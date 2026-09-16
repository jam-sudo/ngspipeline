#!/usr/bin/env python3
"""Deterministic two-sample GEX + assignment fixtures for the TO_ALIVE_H5AD pooling test (docs/decisions/011).

Sample s1: 4 cells (c1 single GENEA, c2 single non-targeting, c3 multi, c4 no guide reads); sample s2: 3 cells
(c1 single GENEB — same barcode as s1/c1 on purpose, c5 single GENEA, c6 unassigned). Same 3-gene index.
Expected pooled h5ad (default, non-single excluded): 4 cells, obs index c1-s1, c2-s1, c1-s2, c5-s2.
"""
import os
here = os.path.dirname(os.path.abspath(__file__))
genes = ["ENSG1.1", "ENSG2.1", "ENSG3.1"]; names = ["GENEA", "GENEB", "GENEC"]
def counts(sample, cells, entries):
    d = os.path.join(here, f"{sample}.count", "counts_filtered"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "cells_x_genes.barcodes.txt"), "w").write("".join(c + "\n" for c in cells))
    open(os.path.join(d, "cells_x_genes.genes.txt"), "w").write("".join(g + "\n" for g in genes))
    open(os.path.join(d, "cells_x_genes.genes.names.txt"), "w").write("".join(n + "\n" for n in names))
    with open(os.path.join(d, "cells_x_genes.mtx"), "w") as f:
        f.write("%%MatrixMarket matrix coordinate real general\n%\n"); f.write(f"{len(cells)} {len(genes)} {len(entries)}\n")
        for r, c, v in entries: f.write(f"{r} {c} {v}\n")
def assignment(sample, rows):
    hdr = ["cell_barcode", "guide_id", "target_gene", "method", "top1_umi", "top2_umi", "ratio", "posterior", "status", "top1_guide_id", "top2_guide_id", "n_assigned", "total_guide_umi"]
    with open(os.path.join(here, f"{sample}.assignment.tsv"), "w") as f:
        f.write("\t".join(hdr) + "\n")
        for r in rows: f.write("\t".join(str(x) for x in r) + "\n")
counts("s1", ["c1", "c2", "c3", "c4"], [(1, 1, 5), (1, 2, 1), (2, 2, 3), (3, 3, 7), (4, 1, 2)])
assignment("s1", [["c1", "V_A", "GENEA", "threshold", 20, 2, 10.0, "", "single", "V_A", "V_B", 1, 22],
                  ["c2", "V_NT", "non-targeting", "threshold", 15, 0, "inf", "", "single", "V_NT", "", 1, 15],
                  ["c3", "", "", "threshold", 12, 11, 1.09, "", "multi", "V_A", "V_B", 2, 23]])
counts("s2", ["c1", "c5", "c6"], [(1, 2, 4), (2, 1, 6), (2, 3, 1), (3, 3, 2)])
assignment("s2", [["c1", "V_B", "GENEB", "threshold", 30, 1, 30.0, "", "single", "V_B", "V_A", 1, 31],
                  ["c5", "V_A", "GENEA", "threshold", 18, 3, 6.0, "", "single", "V_A", "V_B", 1, 21],
                  ["c6", "", "", "threshold", 2, 0, "inf", "", "unassigned", "V_A", "", 0, 2]])
print("written", here)
