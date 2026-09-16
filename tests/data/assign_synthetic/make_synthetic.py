#!/usr/bin/env python3
"""Synthetic guide-count matrix for the GUIDE_ASSIGN unit test (T-13 DoD). Run from the repo root.

Two vectors V1 (guides G1,G2) and V2 (G3,G4). 24 clearly positive cells (12 per vector, 40-60 UMIs,
1-3 UMIs of the other vector), 26 background cells (0-3 UMIs), and five edge cells whose expected
status is fixed by the design for BOTH methods with min_umi=5, min_ratio=3:

| cell | V1 (G1+G2) | V2 (G3+G4) | threshold | mixture |
| --- | --- | --- | --- | --- |
| E1_single     | 50 (30+20) | 1  | single V1 (ratio 50)                    | single V1 (V2=1 is background) |
| E2_multi      | 50         | 45 | multi (ratio 1.11 < 3)                  | multi (both positive)           |
| E3_borderline | 45         | 15 | single V1 (ratio 3.0 >= 3, boundary)    | single V1 (15 is far below the 40-60 positives, so background) |
| E4_zero       | 0          | 0  | unassigned                              | unassigned                      |
| E5_tie        | 50         | 50 | multi (ratio 1.0, top1 == top2)         | multi                           |
Deterministic (fixed pseudo-random sequence via a linear congruential generator, no numpy).
"""
import os, csv
D = os.path.dirname(os.path.abspath(__file__))
def lcg(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % 2**31
        yield x
r = lcg(7)
def pick(lo, hi): return lo + next(r) % (hi - lo + 1)
cells = []  # (barcode, G1, G2, G3, G4)
def bc(i): return "SYN" + format(i, "013d")
for i in range(12):  # V1 positives
    v1 = pick(40, 60); a = pick(10, v1 - 10); v2 = pick(1, 3)
    cells.append((bc(len(cells)), a, v1 - a, v2, 0))
for i in range(12):  # V2 positives
    v2 = pick(40, 60); a = pick(10, v2 - 10); v1 = pick(1, 3)
    cells.append((bc(len(cells)), v1, 0, a, v2 - a))
for i in range(26):  # background
    cells.append((bc(len(cells)), pick(0, 2), pick(0, 1), pick(0, 2), pick(0, 1)))
edge = [("E1_single", 30, 20, 1, 0), ("E2_multi", 25, 25, 20, 25), ("E3_borderline", 25, 20, 10, 5), ("E4_zero", 0, 0, 0, 0), ("E5_tie", 25, 25, 25, 25)]
cells += edge
feats = ["G1", "G2", "G3", "G4"]
entries = [(i + 1, j + 1, c[j + 1]) for i, c in enumerate(cells) for j in range(4) if c[j + 1] > 0]
with open(os.path.join(D, "cells_x_features.mtx"), "w") as f:
    f.write("%%MatrixMarket matrix coordinate real general\n%\n")
    f.write(f"{len(cells)} {len(feats)} {len(entries)}\n")
    for i, j, v in entries: f.write(f"{i} {j} {v}\n")
open(os.path.join(D, "cells_x_features.barcodes.txt"), "w").write("".join(c[0] + "\n" for c in cells))
open(os.path.join(D, "cells_x_features.genes.txt"), "w").write("".join(g + "\n" for g in feats))
open(os.path.join(D, "cells.txt"), "w").write("".join(c[0] + "\n" for c in cells))
with open(os.path.join(D, "feature_map.tsv"), "w") as f:
    f.write("feature\tguide_ids\ttarget_genes\n")
    for g, gene in zip(feats, ["GENEA", "GENEA", "GENEB", "GENEB"]): f.write(f"{g}\t{g}\t{gene}\n")
with open(os.path.join(D, "library.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(["guide_id", "target_gene", "protospacer", "vector_id"])
    w.writerow(["G1", "GENEA", "GACAGACCTAGGACAGGCGG", "V1"]); w.writerow(["G2", "GENEA", "GCTGAGAACAGACCTAGGAC", "V1"])
    w.writerow(["G3", "GENEB", "GTCCGTGGAGCTGGACTTCA", "V2"]); w.writerow(["G4", "GENEB", "GAAGTCCAGCTCCACGGACT", "V2"])
with open(os.path.join(D, "expected.tsv"), "w") as f:
    f.write("cell\tthreshold_status\tthreshold_guide\tmixture_status\tmixture_guide\n")
    f.write("E1_single\tsingle\tV1\tsingle\tV1\nE2_multi\tmulti\tV1\tmulti\tV1\nE3_borderline\tsingle\tV1\tsingle\tV1\nE4_zero\tunassigned\t-\tunassigned\t-\nE5_tie\tmulti\tV1\tmulti\tV1\n")
print(f"wrote {len(cells)} cells x {len(feats)} features, {len(entries)} entries")
