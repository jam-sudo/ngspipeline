// Test harness: GUIDE_INDEX + GUIDE_COUNT on the synthetic guide reads (tests/data/guide_synthetic)
include { GUIDE_INDEX } from '../../modules/local/guide_index/main'
include { GUIDE_COUNT } from '../../modules/local/guide_count/main'

workflow GUIDE_SYNTHETIC {
    take:
    library     // path: guide library CSV
    r1          // path: R1
    r2          // path: R2
    technology  // string
    kite_mode   // string

    main:
    GUIDE_INDEX(channel.value([ [ id: 'synthetic' ], file(library) ]))
    GUIDE_COUNT(channel.value([ [ id: 'synthetic' ], [ file(r1), file(r2) ] ]), GUIDE_INDEX.out.index, GUIDE_INDEX.out.t2g, technology, kite_mode)

    emit:
    matrix   = GUIDE_COUNT.out.matrix
    barcodes = GUIDE_COUNT.out.barcodes
    features = GUIDE_COUNT.out.features
    h5ad     = GUIDE_COUNT.out.h5ad
}
