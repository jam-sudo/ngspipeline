// Assign a guide (vector) to each GEX-called cell from the kite guide counts (T-13; bin/guide_assign.py).
process GUIDE_ASSIGN {
    tag "$meta.id"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/kb-python:0.28.2--pyhdfd78af_2' :
        'quay.io/biocontainers/kb-python:0.28.2--pyhdfd78af_2' }"

    input:
    tuple val(meta), path(mtx), path(barcodes), path(features), path(cells) // guide matrix + GEX-called cell barcodes (or [] for all)
    path feature_map
    path guide_library
    val  method       // threshold | mixture
    val  min_umi
    val  min_ratio

    output:
    tuple val(meta), path("${prefix}.assignment.tsv")        , emit: assignment
    tuple val(meta), path("${prefix}.assignment_summary.tsv"), emit: summary
    tuple val(meta), path("${prefix}_guide_assignment*_mqc.tsv")  , emit: mqc
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), emit: versions_python, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args    = task.ext.args ?: ''
    prefix      = task.ext.prefix ?: "${meta.id}"
    def cells_arg = cells ? "--cells ${cells}" : ''
    """
    guide_assign.py \\
        --mtx ${mtx} \\
        --barcodes ${barcodes} \\
        --features ${features} \\
        --feature-map ${feature_map} \\
        --library ${guide_library} \\
        ${cells_arg} \\
        --method ${method} \\
        --min-umi ${min_umi} \\
        --min-ratio ${min_ratio} \\
        --sample ${meta.id} \\
        $args \\
        --out ${prefix}.assignment.tsv \\
        --summary ${prefix}.assignment_summary.tsv \\
        --mqc ${prefix}_guide_assignment_mqc.tsv
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.assignment.tsv ${prefix}.assignment_summary.tsv ${prefix}_guide_assignment_mqc.tsv ${prefix}_guide_assignment_generalstats_mqc.tsv
    """
}
