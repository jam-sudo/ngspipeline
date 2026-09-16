#!/usr/bin/env python3
"""Independent check of kite guide counts by direct protospacer matching (docs/decisions/005).

Not a pipeline step. For each read pair: cell barcode = R1[:16] translated FB->GEX with the
10x map, UMI = R1[16:28]; the protospacer is looked up as the 20-mer at every offset in a
window of R2 (default 28-36), first exact, then Hamming distance 1. UMIs are collapsed per
(cell, guide) exactly (no error correction), so counts are comparable to bustools' but not
identical by construction. Prints a per-(cell, guide) table to compare with the kite matrix.
"""
import argparse, csv, gzip, itertools, sys, collections, subprocess, io


def fastq(path):
    proc = subprocess.Popen(["gzip", "-dc", path], stdout=subprocess.PIPE)
    f = io.TextIOWrapper(proc.stdout, encoding="ascii")
    for h, s, p, q in itertools.zip_longest(*[f] * 4):
        yield s.rstrip("\n")


def hamming1_variants(seq):
    for i, c in enumerate(seq):
        for b in "ACGT":
            if b != c:
                yield seq[:i] + b + seq[i + 1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r1", required=True); ap.add_argument("--r2", required=True)
    ap.add_argument("--library", required=True); ap.add_argument("--fb-map", help="FB<TAB>GEX map (gz); omit for v2")
    ap.add_argument("--barcodes", help="restrict to these GEX barcodes (one per line)")
    ap.add_argument("--window", default="28-36"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.window.split("-"))
    lib = list(csv.DictReader(open(a.library)))
    exact = {}
    for r in lib:
        exact.setdefault(r["protospacer"].upper(), []).append(r["guide_id"])
    feat = {s: "+".join(g) for s, g in exact.items()}
    ham1 = {}
    for s, name in feat.items():
        for v in hamming1_variants(s):
            if v not in feat:
                ham1.setdefault(v, set()).add(name)
    ham1 = {v: next(iter(n)) for v, n in ham1.items() if len(n) == 1}
    keep = set(l.strip() for l in open(a.barcodes)) if a.barcodes else None
    trans = {}
    if a.fb_map:
        with gzip.open(a.fb_map, "rt") as f:
            for line in f:
                fb, gex = line.split()
                if keep is None or gex in keep:
                    trans[fb] = gex
    umis = collections.defaultdict(set)
    n = hit_exact = hit_ham = miss = nobc = 0
    for s1, s2 in zip(fastq(a.r1), fastq(a.r2)):
        n += 1
        bc = s1[:16]
        if a.fb_map:
            bc = trans.get(bc)
            if bc is None:
                nobc += 1; continue
        elif keep is not None and bc not in keep:
            nobc += 1; continue
        umi = s1[16:28]
        found = None
        for off in range(lo, hi + 1):
            k = s2[off:off + 20]
            if k in feat:
                found = feat[k]; hit_exact += 1; break
        if found is None:
            for off in range(lo, hi + 1):
                k = s2[off:off + 20]
                if k in ham1:
                    found = ham1[k]; hit_ham += 1; break
        if found is None:
            miss += 1; continue
        umis[(bc, found)].add(umi)
    with open(a.out, "w", newline="") as o:
        w = csv.writer(o, delimiter="\t", lineterminator="\n")
        w.writerow(["barcode", "feature", "umis", "reads_exact_or_ham1"])
        for (bc, f), u in sorted(umis.items()):
            w.writerow([bc, f, len(u), ""])
    print(f"reads={n} barcode_not_kept={nobc} exact={hit_exact} ham1={hit_ham} unmatched={miss} "
          f"(cell,guide) pairs={len(umis)} total_umis={sum(len(u) for u in umis.values())}", file=sys.stderr)


if __name__ == "__main__":
    main()
