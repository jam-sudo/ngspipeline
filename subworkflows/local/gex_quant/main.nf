/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    GEX_QUANT: gene-expression quantification with kallisto|bustools (kb-python)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Reference: either a prebuilt kb index directory (--reference_index, containing
    *.idx and t2g.txt) or --fasta + --gtf built in-pipeline by KALLISTOBUSTOOLS_REF.
    Quantification: KALLISTOBUSTOOLS_COUNT (standard workflow, bustools cell filter via
    ext.args). Output is the quantifier's native directory (docs/decisions/002).
*/

include { KALLISTOBUSTOOLS_REF   } from '../../../modules/nf-core/kallistobustools/ref/main'
include { KALLISTOBUSTOOLS_COUNT } from '../../../modules/nf-core/kallistobustools/count/main'

workflow GEX_QUANT {

    take:
    ch_reads        // channel: [ meta, [ r1, r2 ] ]  meta.id, meta.expected_cells
    ch_fasta        // channel: [ meta2, fasta ] or empty
    ch_gtf          // channel: [ meta2, gtf ]   or empty
    reference_index // string: directory with a prebuilt kb index (*.idx + t2g.txt) or null
    technology      // string: kb technology string, e.g. 10XV3
    workflow_mode   // string: kb workflow, 'standard'

    main:

    def ch_versions = channel.empty()
    def ch_index
    def ch_t2g

    if (reference_index) {
        def ref_dir = file(reference_index, checkIfExists: true)
        def idx_files = file("${ref_dir}/*.idx")
        if (!idx_files) {
            error("--reference_index ${reference_index} contains no *.idx file")
        }
        ch_index = channel.value([ [ id: ref_dir.name ], idx_files instanceof List ? idx_files[0] : idx_files ])
        ch_t2g   = channel.value(file("${ref_dir}/t2g.txt", checkIfExists: true))
    } else {
        KALLISTOBUSTOOLS_REF(ch_fasta, ch_gtf, workflow_mode)
        ch_index = KALLISTOBUSTOOLS_REF.out.index
        ch_t2g   = KALLISTOBUSTOOLS_REF.out.t2g
    }

    KALLISTOBUSTOOLS_COUNT(
        ch_reads,
        ch_index,
        ch_t2g,
        [],
        [],
        technology,
        workflow_mode
    )

    // Cells x genes dimensions from the filtered matrix header (Matrix Market: rows cols nnz).
    // Logged per sample; also emitted for MultiQC custom content (T-15) and checks (T-11 DoD).
    def ch_dims = KALLISTOBUSTOOLS_COUNT.out.count
        .map { meta, count_dir ->
            def mtx = file("${count_dir}/counts_filtered/cells_x_genes.mtx")
            if (!mtx.exists()) {
                mtx = file("${count_dir}/counts_unfiltered/cells_x_genes.mtx")
            }
            // Matrix Market: skip '%' comment lines (bounded scan; strict syntax has no while loops)
            def header = mtx.withReader { r ->
                def line = r.readLine()
                (1..50).each { if (line != null && line.startsWith('%')) { line = r.readLine() } }
                line
            }
            def (cells, genes, nnz) = header.trim().split(/\s+/).collect { it as long }
            def frac = meta.expected_cells ? (cells / meta.expected_cells) : null
            log.info "[GEX_QUANT] ${meta.id}: ${cells} cells x ${genes} genes (${nnz} non-zero) in ${mtx.parent.name}" +
                     (frac != null ? String.format("; %.1f%% of expected_cells=%d", frac * 100, meta.expected_cells) : '')
            [ meta, [ cells: cells, genes: genes, nnz: nnz, matrix: mtx.parent.name ] ]
        }

    emit:
    count_dir = KALLISTOBUSTOOLS_COUNT.out.count   // channel: [ meta, path(<id>.count) ]
    matrix    = KALLISTOBUSTOOLS_COUNT.out.matrix  // channel: path(*.mtx)
    dims      = ch_dims                            // channel: [ meta, [cells, genes, nnz, matrix] ]
    index     = ch_index                           // channel: [ meta2, path(*.idx) ]
    t2g       = ch_t2g                             // channel: path(t2g.txt)
    versions  = ch_versions                        // channel: [ path(versions.yml) ]
}
