// Merge GEX counts + guide assignment into the ALIVE-ready h5ad (T-14; bin/to_alive_h5ad.py, docs/alive_schema.md).
process TO_ALIVE_H5AD {
    tag "$meta.id"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/kb-python:0.28.2--pyhdfd78af_2' :
        'quay.io/biocontainers/kb-python:0.28.2--pyhdfd78af_2' }"

    input:
    tuple val(meta), path(counts_dir), path(assignment)
    val   keep_nonsingle

    output:
    tuple val(meta), path("${prefix}.h5ad"), emit: h5ad
    tuple val("${task.process}"), val('anndata'), eval("python3 -c 'import anndata; print(anndata.__version__)'"), emit: versions_anndata, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    prefix   = task.ext.prefix ?: "${meta.id}"
    def keep = keep_nonsingle ? '--keep-nonsingle' : ''
    """
    to_alive_h5ad.py \\
        --counts-dir ${counts_dir} \\
        --assignment ${assignment} \\
        --sample ${meta.id} \\
        --pipeline-version ${workflow.manifest.version} \\
        ${keep} \\
        $args \\
        --out ${prefix}.h5ad
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.h5ad
    """
}
