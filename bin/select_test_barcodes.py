#!/usr/bin/env python3
"""Select cell and background barcodes for the test profile (T-10).

Inputs: the authors' per-cell table for one GEM group (extracted from the
published h5ad), one R1 FASTQ of the same GEM group (to find background
barcodes that are NOT cells), and the 10x feature-barcode translation map.
Output: a TSV committed to assets/test_data/ that make_test_data.py consumes.

Deterministic: cells are chosen by sorted barcode within each vector; background
barcodes by count rank then barcode.
"""
import argparse, csv, gzip, hashlib, collections, itertools, sys

def read_cells(path):
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True, help="TSV with barcode16, sgID_AB, gene (one GEM group)")
    ap.add_argument("--r1", required=True, help="one GEX R1 fastq.gz of the same GEM group")
    ap.add_argument("--fb-map", required=True, help="10x feature-barcode map (FB<TAB>GEX), gz")
    ap.add_argument("--n-vectors", type=int, default=24)
    ap.add_argument("--cells-per-vector", type=int, default=4)
    ap.add_argument("--n-nontargeting", type=int, default=24)
    ap.add_argument("--n-background", type=int, default=300)
    ap.add_argument("--scan-reads", type=int, default=4_000_000)
    ap.add_argument("--gene-totals", help="TSV gene_id, gene_name, total UMI (same GEM group); writes --genes-out")
    ap.add_argument("--n-genes", type=int, default=200)
    ap.add_argument("--genes-out")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cells = read_cells(a.cells)
    by_vec = collections.defaultdict(list)
    for r in cells:
        by_vec[r["sgID_AB"]].append(r)
    nt_key = [k for k in by_vec if k.startswith("non-targeting")]
    targeting = sorted(((k, v) for k, v in by_vec.items() if k not in nt_key),
                       key=lambda kv: (-len(kv[1]), kv[0]))
    chosen = []
    for k, v in targeting[: a.n_vectors]:
        for r in sorted(v, key=lambda r: r["barcode16"])[: a.cells_per_vector]:
            chosen.append((r["barcode16"], "cell", r["sgID_AB"], r["gene"]))
    nt_cells = sorted((r for k in nt_key for r in by_vec[k]), key=lambda r: r["barcode16"])
    for r in nt_cells[: a.n_nontargeting]:
        chosen.append((r["barcode16"], "cell", r["sgID_AB"], r["gene"]))
    cell_set = {r["barcode16"] for r in cells}

    # background: frequent barcodes in R1 that are not cells in the authors' table
    cnt = collections.Counter()
    with gzip.open(a.r1, "rt") as f:
        for i, line in enumerate(itertools.islice(f, 1, None, 4)):
            cnt[line[:16]] += 1
            if i + 1 >= a.scan_reads:
                break
    bg = [(b, c) for b, c in cnt.items() if b not in cell_set and 20 <= c <= 200 and "N" not in b]
    bg.sort(key=lambda bc: (-bc[1], bc[0]))

    # one pass over the translation map: FB variant for chosen cells and background candidates;
    # candidates absent from the whitelist (adapter-derived sequences) are dropped
    need = {b for b, *_ in chosen} | {b for b, _ in bg}
    fb_of = {}
    with gzip.open(a.fb_map, "rt") as f:
        for line in f:
            fb, gex = line.split()
            if gex in need:
                fb_of[gex] = fb
    missing = {b for b, *_ in chosen} - set(fb_of)
    if missing:
        sys.exit(f"{len(missing)} cell barcodes not in whitelist, e.g. {sorted(missing)[:3]}")
    n_cand = len(bg)
    bg = [(b, c) for b, c in bg if b in fb_of]
    for b, c in bg[: a.n_background]:
        chosen.append((b, "background", "", ""))
    with open(a.out, "w", newline="") as o:
        w = csv.writer(o, delimiter="\t")
        w.writerow(["barcode", "fb_barcode", "kind", "sgID_AB", "target_gene"])
        for b, kind, sg, g in chosen:
            w.writerow([b, fb_of[b], kind, sg, g])
    if a.gene_totals and a.genes_out:
        gt = list(csv.DictReader(open(a.gene_totals), delimiter="\t"))
        gt.sort(key=lambda r: (-int(r["total_umi_gg4"]), r["gene_id"]))
        with open(a.genes_out, "w", newline="") as o:
            w = csv.writer(o, delimiter="\t")
            w.writerow(["gene_id", "gene_name", "total_umi_gem_group"])
            for r in gt[: a.n_genes]:
                w.writerow([r["gene_id"], r["gene_name"], r["total_umi_gg4"]])
        print(f"wrote {a.genes_out}: top {a.n_genes} genes by UMI")
    ncell = sum(1 for c in chosen if c[1] == "cell")
    print(f"wrote {a.out}: {ncell} cells ({a.n_vectors} vectors x {a.cells_per_vector} + {a.n_nontargeting} NT), "
          f"{len(chosen)-ncell} background barcodes (from {len(bg)} whitelisted of {n_cand} candidates)")

if __name__ == "__main__":
    main()
