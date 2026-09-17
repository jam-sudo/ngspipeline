#!/usr/bin/env python3
"""Per-cell guide assignment from a cells x features guide-count matrix (T-13).

Counts are aggregated per *vector* (library column `vector_id`; a guide is its own vector
when the column is absent) so dual-guide libraries are assigned at the vector level.

Methods
  threshold  top1 >= --min-umi and top1/top2 >= --min-ratio -> single; top1 >= --min-umi and
             ratio < --min-ratio -> multi; otherwise unassigned. Ratio with top2 == 0 is inf.
  mixture    per vector, a two-component mixture on y = log2(UMI + 1) over cells with UMI > 0:
             background ~ Poisson(lambda) (continuous pmf) and positive ~ Normal(mu, sigma),
             fit by EM with seeded random restarts (best log-likelihood kept), following
             Replogle et al. 2020/2022 (docs/decisions/001). A cell carries the vector when the
             posterior of the positive component > 0.5. Vectors with fewer than --min-cells-fit
             non-zero cells cannot be fit and fall back to `UMI >= --min-umi` for that vector (posterior NaN).
             single = exactly one vector; multi = two or more; unassigned = none.

Output: assignment.tsv with cell_barcode, guide_id (vector), target_gene, method, top1_umi,
top2_umi, ratio, posterior, status, plus top1_guide_id (top vector regardless of status), top2_guide_id, n_assigned, total_guide_umi.
"""
import argparse, csv, math, sys
import numpy as np


def read_mtx(path):
    rows = []
    with open(path) as f:
        header = None
        for line in f:
            if line.startswith("%"):
                continue
            p = line.split()
            if header is None:
                header = tuple(int(x) for x in p[:3]); continue
            rows.append((int(p[0]) - 1, int(p[1]) - 1, float(p[2])))
    return header, rows


def poisson_logpmf_cont(y, lam):
    # continuous extension of the Poisson pmf, lambda^y e^-lambda / Gamma(y+1)
    lam = max(lam, 1e-6)
    return y * math.log(lam) - lam - math.lgamma(y + 1.0)


def normal_logpdf(y, mu, sigma):
    sigma = max(sigma, 1e-3)
    return -0.5 * math.log(2 * math.pi) - math.log(sigma) - 0.5 * ((y - mu) / sigma) ** 2


def fit_mixture(y, rng, restarts=100, iters=200):
    """EM for pi*Poisson(lambda) + (1-pi)*Normal(mu, sigma) on y. Returns (params, loglik)."""
    y = np.asarray(y, dtype=float)
    best = None
    for _ in range(restarts):
        lo, hi = np.quantile(y, [0.25, 0.75])
        lam = max(rng.uniform(0.5, 1.5) * max(lo, 0.3), 0.1)
        mu = rng.uniform(0.8, 1.2) * max(hi, 1.0)
        sigma = max(0.3 * rng.uniform(0.5, 1.5), 0.05)
        pi = rng.uniform(0.3, 0.9)
        ll_old = -np.inf
        for _ in range(iters):
            lp0 = np.array([poisson_logpmf_cont(v, lam) for v in y]) + math.log(max(pi, 1e-9))
            lp1 = np.array([normal_logpdf(v, mu, sigma) for v in y]) + math.log(max(1 - pi, 1e-9))
            m = np.maximum(lp0, lp1)
            ll = float(np.sum(m + np.log(np.exp(lp0 - m) + np.exp(lp1 - m))))
            r1 = 1.0 / (1.0 + np.exp(np.clip(lp0 - lp1, -700, 700)))  # responsibility of the positive component
            r0 = 1.0 - r1
            if r0.sum() < 1e-9 or r1.sum() < 1e-9:
                break
            lam = float(np.sum(r0 * y) / r0.sum())
            mu = float(np.sum(r1 * y) / r1.sum())
            sigma = float(math.sqrt(max(np.sum(r1 * (y - mu) ** 2) / r1.sum(), 1e-4)))
            pi = float(r0.mean())
            if abs(ll - ll_old) < 1e-8:
                break
            ll_old = ll
        # a valid solution has the positive component above the background
        if mu <= lam:
            continue
        if best is None or ll > best[1]:
            best = ((pi, lam, mu, sigma), ll)
    return best


def posterior_positive(y, params):
    pi, lam, mu, sigma = params
    lp0 = poisson_logpmf_cont(y, lam) + math.log(max(pi, 1e-9))
    lp1 = normal_logpdf(y, mu, sigma) + math.log(max(1 - pi, 1e-9))
    d = lp0 - lp1
    if d > 700:
        return 0.0
    if d < -700:
        return 1.0
    return 1.0 / (1.0 + math.exp(d))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mtx", required=True); ap.add_argument("--barcodes", required=True); ap.add_argument("--features", required=True)
    ap.add_argument("--feature-map", required=True, help="feature<TAB>guide_ids<TAB>target_genes (from guide_index)")
    ap.add_argument("--library", required=True, help="guide_id,target_gene,protospacer[,vector_id]")
    ap.add_argument("--cells", help="GEX-called cell barcodes (one per line); assignment is restricted to these")
    ap.add_argument("--method", choices=["threshold", "mixture"], required=True)
    ap.add_argument("--min-umi", type=float, required=True); ap.add_argument("--min-ratio", type=float, required=True)
    ap.add_argument("--min-cells-fit", type=int, default=10); ap.add_argument("--restarts", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--sample", default="sample")
    ap.add_argument("--out", required=True); ap.add_argument("--summary", required=True)
    ap.add_argument("--mqc", help="write a MultiQC custom-content bargraph TSV (*_mqc.tsv)")
    a = ap.parse_args()

    lib = list(csv.DictReader(open(a.library)))
    has_vec = "vector_id" in lib[0]
    vec_of = {r["guide_id"]: (r["vector_id"] if has_vec and r["vector_id"] else r["guide_id"]) for r in lib}
    gene_of_vec = {}
    for r in lib:
        gene_of_vec.setdefault(vec_of[r["guide_id"]], r["target_gene"])
    fmap = {}
    with open(a.feature_map) as f:
        rd = csv.DictReader(f, delimiter="\t")
        for r in rd:
            fmap[r["feature"]] = r["guide_ids"].split(";")
    barcodes = [l.strip() for l in open(a.barcodes)]
    features = [l.strip() for l in open(a.features)]
    header, entries = read_mtx(a.mtx)
    if header[0] != len(barcodes) or header[1] != len(features):
        sys.exit(f"matrix header {header} does not match {len(barcodes)} barcodes x {len(features)} features")
    feat_vecs = []
    for fname in features:
        gids = fmap.get(fname, [fname])
        vecs = sorted({vec_of.get(g, g) for g in gids})
        feat_vecs.append(vecs)
    vectors = sorted({v for vs in feat_vecs for v in vs})
    vidx = {v: i for i, v in enumerate(vectors)}
    cells = [l.strip() for l in open(a.cells)] if a.cells else barcodes
    cell_set = set(cells)
    bidx = {b: i for i, b in enumerate(barcodes)}
    M = np.zeros((len(cells), len(vectors)))
    cidx = {b: i for i, b in enumerate(cells)}
    for i, j, v in entries:
        b = barcodes[i]
        if b not in cell_set:
            continue
        for vec in feat_vecs[j]:  # a merged feature shared by several vectors credits each of them
            M[cidx[b], vidx[vec]] += v

    rng = np.random.default_rng(a.seed)
    post = np.full(M.shape, np.nan)
    fits = {}
    if a.method == "mixture":
        for j, vec in enumerate(vectors):
            nz = np.where(M[:, j] > 0)[0]
            if len(nz) < a.min_cells_fit:
                fits[vec] = None; continue
            y = np.log2(M[nz, j] + 1.0)
            res = fit_mixture(y, rng, restarts=a.restarts)
            fits[vec] = res
            if res is None:
                continue
            for i in nz:
                post[i, j] = posterior_positive(math.log2(M[i, j] + 1.0), res[0])

    status_counts = {"single": 0, "multi": 0, "unassigned": 0}
    with open(a.out, "w", newline="") as o:
        w = csv.writer(o, delimiter="\t", lineterminator="\n")
        w.writerow(["cell_barcode", "guide_id", "target_gene", "method", "top1_umi", "top2_umi", "ratio", "posterior", "status",
                    "top1_guide_id", "top2_guide_id", "n_assigned", "total_guide_umi"])
        for i, b in enumerate(cells):
            row = M[i]
            order = np.argsort(-row, kind="stable")
            top1, top2 = order[0], (order[1] if len(order) > 1 else None)
            t1 = float(row[top1]); t2 = float(row[top2]) if top2 is not None else 0.0
            ratio = (t1 / t2) if t2 > 0 else (math.inf if t1 > 0 else 0.0)
            if a.method == "threshold":
                if t1 < a.min_umi or t1 <= 0:
                    st, n_assigned, chosen, pst = "unassigned", 0, None, float("nan")
                elif ratio >= a.min_ratio:
                    st, n_assigned, chosen, pst = "single", 1, top1, float("nan")
                else:
                    st, n_assigned, chosen, pst = "multi", 2, top1, float("nan")
            else:
                assigned = []
                for j in range(len(vectors)):
                    if row[j] <= 0:
                        continue
                    if fits.get(vectors[j]) is None:  # not fittable: count-only fallback, recorded in the summary
                        if row[j] >= a.min_umi:
                            assigned.append(j)
                    elif post[i, j] > 0.5:
                        assigned.append(j)
                assigned.sort(key=lambda j: -row[j])
                n_assigned = len(assigned)
                st = "single" if n_assigned == 1 else ("multi" if n_assigned > 1 else "unassigned")
                chosen = assigned[0] if assigned else None
                pst = float(post[i, chosen]) if chosen is not None and not np.isnan(post[i, chosen]) else float("nan")
            status_counts[st] += 1
            w.writerow([b, vectors[chosen] if chosen is not None else "", gene_of_vec.get(vectors[chosen], "") if chosen is not None else "",
                        a.method, int(t1), int(t2), ("inf" if ratio == math.inf else f"{ratio:.3f}"),
                        ("" if math.isnan(pst) else f"{pst:.4f}"), st,
                        vectors[top1] if t1 > 0 else "", vectors[top2] if (top2 is not None and t2 > 0) else "", n_assigned, int(row.sum())])
    with open(a.summary, "w") as s:
        s.write(f"sample\t{a.sample}\nmethod\t{a.method}\ncells\t{len(cells)}\nvectors\t{len(vectors)}\n")
        for k, v in status_counts.items():
            s.write(f"{k}\t{v}\n")
        if a.method == "mixture":
            s.write(f"vectors_fit\t{sum(1 for v in fits.values() if v)}\nvectors_fallback\t{sum(1 for v in fits.values() if not v)}\n")
    if a.mqc:
        n = max(len(cells), 1)
        with open(a.mqc, "w") as m:
            m.write("# id: 'guide_assignment'\n# section_name: 'Guide assignment'\n"
                    f"# description: 'Per-cell guide (vector) assignment status from guide_assign.py ({a.method}: min_umi={a.min_umi:g}, min_ratio={a.min_ratio:g}). "
                    "single = one vector, multi = two or more, unassigned = none.'\n"
                    "# plot_type: 'bargraph'\n# pconfig:\n#     id: 'guide_assignment_status'\n#     title: 'Guide assignment: cells by status'\n#     ylab: 'Cells'\n#     cpswitch_counts_label: 'Cells'\n#     cpswitch_percent_label: 'Percent of cells'\n")
            m.write("Sample\tsingle\tmulti\tunassigned\n")
            m.write(f"{a.sample}\t{status_counts['single']}\t{status_counts['multi']}\t{status_counts['unassigned']}\n")
        gs = a.mqc.replace("_mqc.tsv", "_generalstats_mqc.tsv") if a.mqc.endswith("_mqc.tsv") else a.mqc + ".generalstats_mqc.tsv"
        with open(gs, "w") as m:
            m.write("# id: 'guide_assignment_generalstats'\n# plot_type: 'generalstats'\n# pconfig:\n#     guide_single_pct:\n#         title: '% single guide'\n#         description: 'Cells with exactly one assigned guide vector'\n#         min: 0\n#         max: 100\n#         suffix: '%'\n#         format: '{:,.1f}'\n#     guide_multi_pct:\n#         title: '% multi guide'\n#         min: 0\n#         max: 100\n#         suffix: '%'\n#         format: '{:,.1f}'\n#     guide_unassigned_pct:\n#         title: '% unassigned'\n#         min: 0\n#         max: 100\n#         suffix: '%'\n#         format: '{:,.1f}'\n")
            m.write("Sample\tguide_single_pct\tguide_multi_pct\tguide_unassigned_pct\n")
            m.write(f"{a.sample}\t{100*status_counts['single']/n:.2f}\t{100*status_counts['multi']/n:.2f}\t{100*status_counts['unassigned']/n:.2f}\n")
    print(f"[guide_assign] {a.sample} {a.method}: {status_counts} of {len(cells)} cells, {len(vectors)} vectors", file=sys.stderr)


if __name__ == "__main__":
    main()
