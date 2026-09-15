#!/usr/bin/env python3
"""Build the -profile test dataset from the real Perturb-seq sample (T-10).

Subsampling is by cell barcode, then by UMI family: for a selected barcode a
read is kept iff hash(barcode+UMI) falls below a fraction, so every read of a
kept UMI is kept and UMI deduplication behaves as on real data. Reads are never
sampled individually. The reference is a "mini genome": one contig per selected
gene (locus +/- flank) with a GTF rewritten to contig coordinates, so the
pipeline still runs its own index-building step.

Everything is deterministic (fixed hash, sorted iteration, gzip mtime=0), so
`sha256sum` of the outputs is stable across runs and machines.
"""
import argparse, csv, gzip, hashlib, io, itertools, os, re, subprocess, sys, time

FRAC_DEN = 2**32


def keep(bc, umi, frac):
    h = int(hashlib.md5((bc + umi).encode()).hexdigest()[:8], 16)
    return h < frac * FRAC_DEN


def open_gz_out(path):
    raw = open(path, "wb")
    return io.TextIOWrapper(gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9), encoding="ascii", newline="\n")


def fastq_records(path):
    # external gzip is several times faster than Python's gzip module on 15 GB of input
    proc = subprocess.Popen(["gzip", "-dc", path], stdout=subprocess.PIPE, bufsize=1 << 20)
    f = io.TextIOWrapper(proc.stdout, encoding="ascii")
    for h, s, p, q in itertools.zip_longest(*[f] * 4):
        yield h.rstrip("\n"), s.rstrip("\n"), q.rstrip("\n")
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"gzip -dc failed on {path}")


def extract_reads(runs, fastq_dir, barcodes, frac_of, out_r1, out_r2, tag):
    n_in = n_out = 0
    per_bc = {}
    with open_gz_out(out_r1) as o1, open_gz_out(out_r2) as o2:
        for run in runs:
            p1 = os.path.join(fastq_dir, f"{run}_1.fastq.gz")
            p2 = os.path.join(fastq_dir, f"{run}_2.fastq.gz")
            for (h1, s1, q1), (h2, s2, q2) in zip(fastq_records(p1), fastq_records(p2)):
                n_in += 1
                bc = s1[:16]
                frac = frac_of.get(bc)
                if frac is None:
                    continue
                if not keep(bc, s1[16:28], frac):
                    continue
                n_out += 1
                per_bc[bc] = per_bc.get(bc, 0) + 1
                rid = f"@{tag}_{run}_{n_in}"
                o1.write(f"{rid}/1\n{s1}\n+\n{q1}\n")
                o2.write(f"{rid}/2\n{s2}\n+\n{q2}\n")
    return n_in, n_out, per_bc


def parse_attr(attrs, key):
    m = re.search(rf'{key} "([^"]+)"', attrs)
    return m.group(1) if m else None


def mini_genome(fasta_gz, gtf_gz, gene_ids, flank, out_fa, out_gtf):
    spans = {}
    lines_by_gene = {}
    with gzip.open(gtf_gz, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            gid = parse_attr(parts[8], "gene_id")
            if gid not in gene_ids or parts[2] not in ("gene", "transcript", "exon"):
                continue
            lines_by_gene.setdefault(gid, []).append(parts)
            if parts[2] == "gene":
                spans[gid] = (parts[0], int(parts[3]), int(parts[4]))
    missing = gene_ids - set(spans)
    if missing:
        sys.exit(f"{len(missing)} selected genes not in GTF, e.g. {sorted(missing)[:3]}")
    by_chrom = {}
    for gid, (chrom, s, e) in spans.items():
        by_chrom.setdefault(chrom, []).append(gid)
    seqs = {}
    with gzip.open(fasta_gz, "rt") as f:
        cur = None
        buf = []
        def flush():
            if cur in by_chrom:
                seqs[cur] = "".join(buf)
        for line in f:
            if line.startswith(">"):
                flush()
                cur = line[1:].split()[0]
                buf = []
            elif cur in by_chrom:
                buf.append(line.strip())
        flush()
    with open_gz_out(out_fa) as fa, open_gz_out(out_gtf) as gt:
        for gid in sorted(spans):
            chrom, s, e = spans[gid]
            cs = max(1, s - flank)
            ce = min(len(seqs[chrom]), e + flank)
            seq = seqs[chrom][cs - 1:ce]
            fa.write(f">{gid} {chrom}:{cs}-{ce}\n")
            for i in range(0, len(seq), 60):
                fa.write(seq[i:i + 60] + "\n")
            shift = cs - 1
            for parts in lines_by_gene[gid]:
                p = list(parts)
                p[0] = gid
                p[3] = str(int(p[3]) - shift)
                p[4] = str(int(p[4]) - shift)
                gt.write("\t".join(p) + "\n")
    return len(spans)


def write_guide_library(pairs_csv, selected_vectors, extra_vectors, out_csv):
    rows = list(csv.DictReader(open(pairs_csv)))
    by_pair = {r["pair_id"]: r for r in rows}
    by_sg = {f'{r["sgID_A"]}|{r["sgID_B"]}': r for r in rows}
    chosen = []
    for sg in sorted(selected_vectors):
        r = by_sg.get(sg)
        if r is None:
            sys.exit(f"vector {sg} not in library")
        chosen.append(r)
    have = {f'{r["sgID_A"]}|{r["sgID_B"]}' for r in chosen}
    for r in sorted(rows, key=lambda r: r["pair_id"]):
        if len(chosen) >= len(selected_vectors) + extra_vectors:
            break
        key = f'{r["sgID_A"]}|{r["sgID_B"]}'
        if key not in have and r["gene"] != "non-targeting":
            chosen.append(r); have.add(key)
    with open(out_csv, "w", newline="") as o:
        w = csv.writer(o, lineterminator="\n")
        w.writerow(["guide_id", "target_gene", "protospacer", "vector_id"])
        for r in chosen:
            vid = f'{r["sgID_A"]}|{r["sgID_B"]}'
            w.writerow([r["sgID_A"], r["gene"], r["protospacer_A"], vid])
            w.writerow([r["sgID_B"], r["gene"], r["protospacer_B"], vid])
    return len(chosen)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fastq-dir", required=True)
    ap.add_argument("--runs", required=True, help="TSV: run_accession<TAB>library (gex|guide)")
    ap.add_argument("--selection", required=True, help="assets/test_data/selected_barcodes.tsv")
    ap.add_argument("--genes", required=True, help="assets/test_data/selected_genes.tsv")
    ap.add_argument("--fasta", required=True, help="Ensembl primary assembly FASTA (gz)")
    ap.add_argument("--gtf", required=True, help="Ensembl GTF (gz)")
    ap.add_argument("--library-pairs", required=True, help="K562_day6_essential_library_pairs.csv")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--gex-frac", type=float, default=0.05, help="UMI-family keep fraction for selected cells (GEX)")
    ap.add_argument("--bg-frac", type=float, default=1.0, help="keep fraction for background barcodes (GEX)")
    ap.add_argument("--guide-frac", type=float, default=0.2, help="UMI-family keep fraction (guide library)")
    ap.add_argument("--flank", type=int, default=500)
    ap.add_argument("--extra-vectors", type=int, default=6, help="library vectors absent from the cells (zero columns)")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(os.path.join(a.outdir, "ref"), exist_ok=True)

    runs = {"gex": [], "guide": []}
    for line in open(a.runs):
        if line.strip() and not line.startswith("#"):
            run, lib = line.split()[:2]
            runs[lib].append(run)
    sel = list(csv.DictReader(open(a.selection), delimiter="\t"))
    gex_frac = {}
    fb_frac = {}
    vectors = set()
    for r in sel:
        if r["kind"] == "cell":
            gex_frac[r["barcode"]] = a.gex_frac
            fb_frac[r["fb_barcode"]] = a.guide_frac
            vectors.add(r["sgID_AB"])
        else:
            gex_frac[r["barcode"]] = a.bg_frac
            fb_frac[r["fb_barcode"]] = a.guide_frac
    genes = {r["gene_id"] for r in csv.DictReader(open(a.genes), delimiter="\t")}

    g_in, g_out, g_per = extract_reads(sorted(runs["gex"]), a.fastq_dir, gex_frac, gex_frac,
                                       os.path.join(a.outdir, "gex_R1.fastq.gz"), os.path.join(a.outdir, "gex_R2.fastq.gz"), "gex")
    s_in, s_out, s_per = extract_reads(sorted(runs["guide"]), a.fastq_dir, fb_frac, fb_frac,
                                       os.path.join(a.outdir, "guide_R1.fastq.gz"), os.path.join(a.outdir, "guide_R2.fastq.gz"), "guide")
    n_genes = mini_genome(a.fasta, a.gtf, genes, a.flank,
                          os.path.join(a.outdir, "ref", "mini_genome.fa.gz"), os.path.join(a.outdir, "ref", "mini_genome.gtf.gz"))
    n_vec = write_guide_library(a.library_pairs, vectors, a.extra_vectors, os.path.join(os.path.dirname(a.outdir.rstrip("/")), "guide_library_test.csv"))

    cells = [r["barcode"] for r in sel if r["kind"] == "cell"]
    with open(os.path.join(a.outdir, "STATS.txt"), "w") as st:
        st.write(f"gex reads in={g_in} out={g_out}; cells with reads={sum(1 for b in cells if b in g_per)}/{len(cells)}\n")
        st.write(f"guide reads in={s_in} out={s_out}; cells with guide reads={sum(1 for r in sel if r['kind']=='cell' and r['fb_barcode'] in s_per)}/{len(cells)}\n")
        st.write(f"mini genome genes={n_genes} flank={a.flank}; library vectors={n_vec}\n")
        st.write(f"params gex_frac={a.gex_frac} bg_frac={a.bg_frac} guide_frac={a.guide_frac}\n")
    generated = ["gex_R1.fastq.gz", "gex_R2.fastq.gz", "guide_R1.fastq.gz", "guide_R2.fastq.gz",
                 "ref/mini_genome.fa.gz", "ref/mini_genome.gtf.gz"]
    with open(os.path.join(a.outdir, "SHA256SUMS"), "w") as sh:
        for rel in generated:
            sh.write(f"{sha256(os.path.join(a.outdir, rel))}  {rel}\n")
    print(open(os.path.join(a.outdir, "STATS.txt")).read(), f"elapsed {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
