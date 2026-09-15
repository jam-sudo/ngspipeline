// Build a kallisto|bustools "kite" feature index from the guide library (docs/decisions/005).
// Every protospacer becomes a feature; kb ref --workflow kite adds all Hamming-distance-1
// variants so one sequencing error in the protospacer still counts.
process GUIDE_INDEX {
    tag "$meta.id"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/kb-python:0.28.2--pyhdfd78af_2' :
        'quay.io/biocontainers/kb-python:0.28.2--pyhdfd78af_2' }"

    input:
    tuple val(meta), path(guide_library) // CSV: guide_id,target_gene,protospacer[,vector_id]

    output:
    tuple val(meta), path("kite.idx")      , emit: index
    path "t2g.txt"                         , emit: t2g
    path "features.tsv"                    , emit: features   // protospacer <TAB> feature name, as indexed
    path "feature_map.tsv"                 , emit: feature_map // feature name <TAB> guide_id(s) <TAB> target_gene(s)
    path "mismatch.fa"                     , emit: mismatch_fasta
    tuple val("${task.process}"), val('kallistobustools'), eval("kb --version 2>&1 | sed -n 's/kb_python //p'"), emit: versions_kallistobustools, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    # protospacers shared by several guides are indexed once under a joined name (A+B);
    # feature_map.tsv keeps the original guide ids and target genes for downstream steps
    python3 - <<'PY'
    import csv, collections, sys
    rows = list(csv.DictReader(open("${guide_library}")))
    need = {"guide_id", "target_gene", "protospacer"}
    if not need <= set(rows[0].keys()):
        sys.exit(f"guide library must have columns {sorted(need)}; got {list(rows[0].keys())}")
    by_seq = collections.OrderedDict()
    lengths = collections.Counter()
    for r in rows:
        seq = r["protospacer"].strip().upper()
        if not seq or set(seq) - set("ACGT"):
            sys.exit(f"invalid protospacer for {r['guide_id']}: {seq!r}")
        lengths[len(seq)] += 1
        by_seq.setdefault(seq, []).append(r)
    if len(lengths) != 1:
        sys.exit(f"protospacers must all have the same length for a kite index; found lengths {dict(lengths)}")
    dup = sum(1 for v in by_seq.values() if len(v) > 1)
    with open("features.tsv", "w") as f, open("feature_map.tsv", "w") as m:
        m.write("feature\\tguide_ids\\ttarget_genes\\n")
        for seq, rs in by_seq.items():
            name = "+".join(r["guide_id"] for r in rs)
            f.write(f"{seq}\\t{name}\\n")
            m.write(name + "\\t" + ";".join(r["guide_id"] for r in rs) + "\\t" + ";".join(dict.fromkeys(r["target_gene"] for r in rs)) + "\\n")
    print(f"guide library: {len(rows)} guides, {len(by_seq)} unique protospacers of length {list(lengths)[0]}, {dup} shared sequences merged", file=sys.stderr)
    PY

    kb ref \\
        --workflow kite \\
        -i kite.idx \\
        -g t2g.txt \\
        -f1 mismatch.fa \\
        -t $task.cpus \\
        $args \\
        features.tsv
    """

    stub:
    """
    touch kite.idx t2g.txt features.tsv feature_map.tsv mismatch.fa
    """
}
