// Count guide (sgRNA) UMIs per cell with kallisto|bustools kite (docs/decisions/005).
// For 10x 3' v3 the feature-barcode library carries the other barcode variant of each gel bead;
// `kite:10xFB` translates it to the gene-expression barcode so the matrix joins directly to GEX.
process GUIDE_COUNT {
    tag "$meta.id"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/kb-python:0.28.2--pyhdfd78af_2' :
        'quay.io/biocontainers/kb-python:0.28.2--pyhdfd78af_2' }"

    input:
    tuple val(meta), path(reads)   // [ guide_r1, guide_r2 ]
    tuple val(meta2), path(index)  // kite.idx
    path  t2g
    val   technology               // 10XV2 | 10XV3
    val   workflow_mode            // kite | kite:10xFB

    output:
    tuple val(meta), path("${prefix}.guide_count")                                , emit: count_dir
    tuple val(meta), path("${prefix}.guide_count/guide_counts.h5ad")              , emit: h5ad
    tuple val(meta), path("${prefix}.guide_count/counts_unfiltered/cells_x_features.mtx"), emit: matrix
    tuple val(meta), path("${prefix}.guide_count/counts_unfiltered/cells_x_features.barcodes.txt"), emit: barcodes
    tuple val(meta), path("${prefix}.guide_count/counts_unfiltered/cells_x_features.genes.txt")   , emit: features
    tuple val("${task.process}"), val('kallistobustools'), eval("kb --version 2>&1 | sed -n 's/kb_python //p'"), emit: versions_kallistobustools, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args   = task.ext.args ?: ''
    prefix     = task.ext.prefix ?: "${meta.id}"
    def memory = task.memory.toGiga() - 1
    """
    kb count \\
        -t $task.cpus \\
        -m ${memory}G \\
        -i $index \\
        -g $t2g \\
        -x $technology \\
        --workflow $workflow_mode \\
        --h5ad \\
        $args \\
        -o ${prefix}.guide_count \\
        ${reads.join(' ')}

    # all barcodes are kept (no cell filter here): cell calling comes from the GEX matrix
    cp ${prefix}.guide_count/counts_unfiltered/adata.h5ad ${prefix}.guide_count/guide_counts.h5ad
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """
    mkdir -p ${prefix}.guide_count/counts_unfiltered
    touch ${prefix}.guide_count/guide_counts.h5ad
    touch ${prefix}.guide_count/counts_unfiltered/cells_x_features.{mtx,barcodes.txt,genes.txt}
    """
}
