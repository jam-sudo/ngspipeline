/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    GUIDE_QUANT: guide library -> kite feature index -> cells x guides counts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GUIDE_INDEX } from '../../../modules/local/guide_index/main'
include { GUIDE_COUNT } from '../../../modules/local/guide_count/main'

workflow GUIDE_QUANT {

    take:
    ch_reads      // channel: [ meta, [ guide_r1, guide_r2 ] ]
    guides        // string: guide library CSV (guide_id,target_gene,protospacer[,vector_id])
    technology    // string: 10XV2 | 10XV3
    ch_gex_dims   // channel: [ meta, [cells, genes, nnz, matrix] ] from GEX_QUANT (for the overlap log)
    ch_gex_counts // channel: [ meta, path(<id>.count) ] from GEX_QUANT

    main:

    def ch_versions = channel.empty()
    def ch_library  = channel.value([ [ id: file(guides).baseName ], file(guides, checkIfExists: true) ])

    GUIDE_INDEX(ch_library)

    // 10x 3' v3 feature-barcode reads carry the second barcode variant: kite:10xFB translates them (001, 005)
    def kite_mode = technology.toUpperCase() == '10XV3' ? 'kite:10xFB' : 'kite'
    GUIDE_COUNT(ch_reads, GUIDE_INDEX.out.index, GUIDE_INDEX.out.t2g, technology, kite_mode)

    // Checks (T-12 DoD): feature columns == unique protospacers; guide barcodes vs GEX barcodes
    def n_features = GUIDE_INDEX.out.features.map { f -> f.readLines().size() }
    def ch_stats = GUIDE_COUNT.out.matrix
        .join(GUIDE_COUNT.out.barcodes)
        .join(ch_gex_counts)
        .combine(n_features)
        .map { meta, mtx, bcs, gex_dir, nfeat ->
            def header = mtx.withReader { r ->
                def line = r.readLine()
                (1..50).each { if (line != null && line.startsWith('%')) { line = r.readLine() } }
                line
            }
            def (n_bc, n_col, nnz) = header.trim().split(/\s+/).collect { it as long }
            def guide_bcs = bcs.readLines().collect { it.trim() } as Set
            def gex_filt  = file("${gex_dir}/counts_filtered/cells_x_genes.barcodes.txt")
            def gex_unf   = file("${gex_dir}/counts_unfiltered/cells_x_genes.barcodes.txt")
            def cells     = gex_filt.exists() ? (gex_filt.readLines().collect { it.trim() } as Set) : ([] as Set)
            def all_gex   = gex_unf.readLines().collect { it.trim() } as Set
            def in_cells  = guide_bcs.intersect(cells).size()
            def in_any    = guide_bcs.intersect(all_gex).size()
            def cells_with_guides = cells ? cells.intersect(guide_bcs).size() : 0
            log.info "[GUIDE_QUANT] ${meta.id}: ${n_bc} barcodes x ${n_col} features (${nnz} non-zero); " +
                     "features == library protospacers: ${n_col == nfeat} (${nfeat}); " +
                     "guide barcodes in GEX cells: ${in_cells}/${n_bc}, in any GEX barcode: ${in_any}/${n_bc}; " +
                     "GEX cells with guide reads: ${cells_with_guides}/${cells.size()}"
            if (n_col != nfeat) {
                error("GUIDE_QUANT ${meta.id}: matrix has ${n_col} feature columns but the library has ${nfeat} unique protospacers")
            }
            [ meta, [ barcodes: n_bc, features: n_col, nnz: nnz, in_cells: in_cells, in_any: in_any,
                      cells: cells.size(), cells_with_guides: cells_with_guides ] ]
        }

    emit:
    h5ad        = GUIDE_COUNT.out.h5ad        // channel: [ meta, guide_counts.h5ad ]
    count_dir   = GUIDE_COUNT.out.count_dir   // channel: [ meta, path(<id>.guide_count) ]
    matrix      = GUIDE_COUNT.out.matrix
    barcodes    = GUIDE_COUNT.out.barcodes
    features    = GUIDE_COUNT.out.features
    feature_map = GUIDE_INDEX.out.feature_map // path: feature <TAB> guide_ids <TAB> target_genes
    stats       = ch_stats                    // channel: [ meta, map ]
    versions    = ch_versions
}
