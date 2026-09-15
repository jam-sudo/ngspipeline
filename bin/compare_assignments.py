#!/usr/bin/env python3
"""Compare the pipeline's per-cell guide assignment with the authors' published identities (T-16).

Inputs: assignment.tsv (guide_assign.py), the authors' per-cell table for the same GEM group
(barcode16, sgID_AB, gene; e.g. extracted from the published h5ad obs), and optionally the GEX
matrix barcodes (unfiltered / filtered) to classify cells the pipeline did not call.
Output: a markdown table of concordance and a categorised discordance table; nothing is tuned
(CLAUDE.md rule 6) — the numbers are findings.

Categories for cells in both tables (authors' call is always a single vector):
  concordant            pipeline single, same vector
  concordant_gene       pipeline single, different vector but same target gene (shared protospacer / paralog)
  discordant_vector     pipeline single, different vector and gene
  multi_pipeline        pipeline multi (authors single): top-1 is the authors' vector or not (sub-flag)
  unassigned_threshold  pipeline unassigned with top-1 == authors' vector but top-1 UMI < min_umi (threshold boundary)
  unassigned_other      pipeline unassigned, top-1 differs or no guide reads
Cells only in the authors' table: not_called_by_pipeline (barcode absent from the GEX filtered matrix)
or filtered_by_pipeline (present in unfiltered but not in filtered). Cells only in the pipeline: not_in_authors.
"""
import argparse, csv, collections


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--assignment", required=True)
    ap.add_argument("--authors", required=True, help="TSV with columns barcode16, sgID_AB, gene")
    ap.add_argument("--unfiltered-barcodes", help="GEX counts_unfiltered barcodes.txt")
    ap.add_argument("--filtered-barcodes", help="GEX counts_filtered barcodes.txt")
    ap.add_argument("--min-umi", type=float, required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--out", required=True, help="markdown report")
    ap.add_argument("--discordant-out", help="TSV of every non-concordant cell")
    a = ap.parse_args()

    pipe = {r["cell_barcode"]: r for r in csv.DictReader(open(a.assignment), delimiter="\t")}
    auth = {r["barcode16"]: r for r in csv.DictReader(open(a.authors), delimiter="\t")}
    unf = set(l.strip() for l in open(a.unfiltered_barcodes)) if a.unfiltered_barcodes else None
    filt = set(l.strip() for l in open(a.filtered_barcodes)) if a.filtered_barcodes else set(pipe)

    cats = collections.Counter()
    rows = []
    common = set(pipe) & set(auth)
    for b in sorted(common):
        p, q = pipe[b], auth[b]
        av, ag = q["sgID_AB"], q["gene"]
        st = p["status"]; pv = p["guide_id"]; pg = p["target_gene"]; t1 = float(p["top1_umi"]); top2 = p.get("top2_guide_id", "")
        if st == "single":
            cat = "concordant" if pv == av else ("concordant_gene" if pg == ag else "discordant_vector")
        elif st == "multi":
            cat = "multi_pipeline_top1_matches" if pv == av else ("multi_pipeline_top2_matches" if top2 == av else "multi_pipeline_other")
        else:
            cat = "unassigned_threshold" if (pv == av and 0 < t1 < a.min_umi) else "unassigned_other"
        cats[cat] += 1
        if cat != "concordant":
            rows.append([b, cat, av, ag, st, pv, pg, p["top1_umi"], p["top2_umi"], p["ratio"], top2])
    for b in sorted(set(auth) - set(pipe)):
        if unf is not None and b in unf and b not in filt:
            cat = "filtered_by_pipeline"
        else:
            cat = "not_called_by_pipeline"
        cats[cat] += 1
        rows.append([b, cat, auth[b]["sgID_AB"], auth[b]["gene"], "", "", "", "", "", "", ""])
    for b in sorted(set(pipe) - set(auth)):
        cats["not_in_authors"] += 1
    n_common = len(common)
    single = sum(1 for b in common if pipe[b]["status"] == "single")
    conc = cats["concordant"]
    with open(a.out, "w") as o:
        o.write(f"## Guide assignment vs authors {a.label}\n\n")
        o.write(f"| quantity | value |\n| --- | --- |\n")
        o.write(f"| authors' cells (GEM group) | {len(auth)} |\n| pipeline cells (GEX filtered) | {len(pipe)} |\n| common barcodes | {n_common} |\n")
        o.write(f"| pipeline single among common | {single} ({100*single/max(n_common,1):.1f}%) |\n")
        o.write(f"| concordant (single, same vector) | {conc} = {100*conc/max(n_common,1):.1f}% of common, {100*conc/max(single,1):.1f}% of pipeline-single |\n")
        o.write(f"| concordant at gene level (same target gene) | {conc + cats['concordant_gene']} ({100*(conc+cats['concordant_gene'])/max(n_common,1):.1f}% of common) |\n\n")
        o.write("| category | cells | % of common |\n| --- | --- | --- |\n")
        for k, v in sorted(cats.items(), key=lambda kv: -kv[1]):
            o.write(f"| {k} | {v} | {100*v/max(n_common,1):.1f} |\n")
    if a.discordant_out:
        with open(a.discordant_out, "w", newline="") as o:
            w = csv.writer(o, delimiter="\t", lineterminator="\n")
            w.writerow(["cell_barcode", "category", "authors_vector", "authors_gene", "pipeline_status", "pipeline_vector", "pipeline_gene", "top1_umi", "top2_umi", "ratio", "top2_vector"])
            w.writerows(rows)
    print(open(a.out).read())


if __name__ == "__main__":
    main()
