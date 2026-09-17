/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { FASTQC                 } from '../modules/nf-core/fastqc/main'
include { MULTIQC                } from '../modules/nf-core/multiqc/main'
include { GEX_QUANT              } from '../subworkflows/local/gex_quant/main'
include { GUIDE_QUANT            } from '../subworkflows/local/guide_quant/main'
include { GUIDE_ASSIGN           } from '../modules/local/guide_assign/main'
include { TO_ALIVE_H5AD          } from '../modules/local/to_alive_h5ad/main'
include { TO_ALIVE_H5AD as TO_ALIVE_H5AD_POOLED } from '../modules/local/to_alive_h5ad/main'
include { paramsSummaryMap       } from 'plugin/nf-schema'
include { paramsSummaryMultiqc   } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText } from '../subworkflows/local/utils_nfcore_ngspipeline_pipeline'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow NGSPIPELINE {

    take:
    ch_samplesheet  // channel: [ meta, [gex_r1, gex_r2], [guide_r1, guide_r2] ] from --input
    guides          // string: guide library CSV
    fasta           // string: genome FASTA (with gtf, builds the kb index) or null
    gtf             // string: annotation GTF or null
    reference_index // string: prebuilt kb index directory or null
    chemistry       // string: kb technology string (10XV2, 10XV3)
    kb_workflow     // string: kb workflow ('standard')
    assign_method   // string: threshold | mixture
    min_umi         // number: guide assignment minimum top-1 UMI
    min_ratio       // number: guide assignment minimum top-1/top-2 ratio
    keep_nonsingle  // boolean: keep multi/unassigned cells in the ALIVE h5ad (006)
    pool_alive      // boolean: also write alive/pooled.h5ad with every sample (011)
    multiqc_config
    multiqc_logo
    multiqc_methods_description
    outdir

    main:

    def ch_versions = channel.empty()
    def ch_multiqc_files = channel.empty()

    def ch_gex   = ch_samplesheet.map { meta, gex, _guide -> [ meta, gex ] }
    def ch_guide = ch_samplesheet.map { meta, _gex, guide -> [ meta, guide ] }

    //
    // MODULE: Run FastQC on both libraries (ids suffixed so reports stay distinct)
    //
    FASTQC(
        ch_gex.map   { meta, reads -> [ meta + [ id: "${meta.id}_gex",   library: 'gex'   ], reads ] }
        .mix(ch_guide.map { meta, reads -> [ meta + [ id: "${meta.id}_guide", library: 'guide' ], reads ] })
    )
    ch_multiqc_files = ch_multiqc_files.mix(FASTQC.out.zip.map{ _meta, file -> file })

    //
    // SUBWORKFLOW: GEX quantification (kallisto|bustools)
    //
    def ch_fasta = fasta ? channel.value([ [ id: file(fasta).baseName ], file(fasta, checkIfExists: true) ]) : channel.empty()
    def ch_gtf   = gtf   ? channel.value([ [ id: file(gtf).baseName ],   file(gtf,   checkIfExists: true) ]) : channel.empty()
    GEX_QUANT(ch_gex, ch_fasta, ch_gtf, reference_index, chemistry, kb_workflow)
    ch_versions = ch_versions.mix(GEX_QUANT.out.versions)

    //
    // SUBWORKFLOW: guide (sgRNA) quantification (kite)
    //
    GUIDE_QUANT(ch_guide, guides, chemistry, GEX_QUANT.out.dims, GEX_QUANT.out.count_dir)
    ch_versions = ch_versions.mix(GUIDE_QUANT.out.versions)

    //
    // MODULE: per-cell guide assignment on GEX-called cells
    //
    def ch_gex_cells = GEX_QUANT.out.count_dir.map { meta, dir ->
        def f = file("${dir}/counts_filtered/cells_x_genes.barcodes.txt")
        [ meta, f.exists() ? f : file("${dir}/counts_unfiltered/cells_x_genes.barcodes.txt") ]
    }
    def ch_assign_in = GUIDE_QUANT.out.matrix
        .join(GUIDE_QUANT.out.barcodes)
        .join(GUIDE_QUANT.out.features)
        .join(ch_gex_cells)
    GUIDE_ASSIGN(ch_assign_in, GUIDE_QUANT.out.feature_map, file(guides, checkIfExists: true), assign_method, min_umi, min_ratio)
    ch_multiqc_files = ch_multiqc_files.mix(GUIDE_ASSIGN.out.mqc.map { _meta, f -> f }.flatten())

    //
    // MODULE: ALIVE-ready h5ad (counts + assignment; docs/alive_schema.md, 006)
    //
    def ch_alive_in = GEX_QUANT.out.count_dir.join(GUIDE_ASSIGN.out.assignment)
    TO_ALIVE_H5AD(ch_alive_in.map { meta, count_dir, assignment -> [ meta, [ meta.id ], count_dir, assignment ] }, keep_nonsingle)

    // Pooled h5ad across samples (GEM groups) for ALIVE (docs/decisions/011): obs index <barcode>-<sample_id>
    def ch_pooled = pool_alive
        ? ch_alive_in.toSortedList { a, b -> a[0].id <=> b[0].id }
            .filter { it.size() > 1 }
            .map { rows -> [ [ id: 'pooled' ], rows.collect { it[0].id }, rows.collect { it[1] }, rows.collect { it[2] } ] }
        : channel.empty()
    TO_ALIVE_H5AD_POOLED(ch_pooled, keep_nonsingle)

    //
    // MultiQC custom content: quantifier statistics (kb count run_info.json / inspect.json + matrix dimensions)
    //
    def ch_kb_mqc = GEX_QUANT.out.count_dir.join(GEX_QUANT.out.dims).join(GUIDE_QUANT.out.count_dir).join(GUIDE_QUANT.out.stats)
        .map { meta, gex_dir, dims, guide_dir, gstats -> kbQuantMqc(meta, gex_dir, dims, guide_dir, gstats) }
        .collectFile(name: 'kb_quant_mqc.tsv', keepHeader: true, skip: kbQuantMqcHeaderLines(), newLine: false)
    ch_multiqc_files = ch_multiqc_files.mix(ch_kb_mqc)

    //
    // Collate and save software versions
    //
    def topic_versions = channel.topic("versions")
        .distinct()
        .branch { entry ->
            versions_file: entry instanceof Path
            versions_tuple: true
        }

    def topic_versions_string = topic_versions.versions_tuple
        .map { process, tool, version ->
            [ process[process.lastIndexOf(':')+1..-1], "  ${tool}: ${version}" ]
        }
        .groupTuple(by:0)
        .map { process, tool_versions ->
            tool_versions.unique().sort()
            "${process}:\n${tool_versions.join('\n')}"
        }

    def ch_collated_versions = softwareVersionsToYAML(ch_versions.mix(topic_versions.versions_file))
        .mix(topic_versions_string)
        .collectFile(
            storeDir: "${outdir}/pipeline_info",
            name:  'ngspipeline_software_'  + 'mqc_'  + 'versions.yml',
            sort: true,
            newLine: true
        )

    //
    // MODULE: MultiQC
    //
    ch_multiqc_files = ch_multiqc_files.mix(ch_collated_versions)
    def ch_summary_params = paramsSummaryMap(workflow, parameters_schema: "nextflow_schema.json")
    def ch_workflow_summary = channel.value(paramsSummaryMultiqc(ch_summary_params))
    ch_multiqc_files = ch_multiqc_files.mix(ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    def ch_multiqc_custom_methods_description = multiqc_methods_description
        ? file(multiqc_methods_description, checkIfExists: true)
        : file("${projectDir}/assets/methods_description_template.yml", checkIfExists: true)
    def ch_methods_description = channel.value(methodsDescriptionText(ch_multiqc_custom_methods_description))
    ch_multiqc_files = ch_multiqc_files.mix(ch_methods_description.collectFile(name: 'methods_description_mqc.yaml', sort: true))
    MULTIQC(
        ch_multiqc_files.flatten().collect().map { files ->
            [
                [id: 'ngspipeline'],
                files,
                multiqc_config
                    ? file(multiqc_config, checkIfExists: true)
                    : file("${projectDir}/assets/multiqc_config.yml", checkIfExists: true),
                multiqc_logo ? file(multiqc_logo, checkIfExists: true) : [],
                [],
                [],
            ]
        }
    )
    emit:multiqc_report = MULTIQC.out.report.map { _meta, report -> [report] }.toList() // channel: /path/to/multiqc_report.html
    gex_counts     = GEX_QUANT.out.count_dir    // channel: [ meta, path(<id>.count) ]
    gex_dims       = GEX_QUANT.out.dims         // channel: [ meta, [cells, genes, nnz, matrix] ]
    guide_h5ad     = GUIDE_QUANT.out.h5ad       // channel: [ meta, guide_counts.h5ad ]
    guide_stats    = GUIDE_QUANT.out.stats      // channel: [ meta, map ]
    assignment     = GUIDE_ASSIGN.out.assignment // channel: [ meta, assignment.tsv ]
    alive_h5ad     = TO_ALIVE_H5AD.out.h5ad     // channel: [ meta, <sample>.h5ad ]
    alive_pooled   = TO_ALIVE_H5AD_POOLED.out.h5ad // channel: [ meta, pooled.h5ad ] (only with --pool_alive and > 1 sample)
    versions       = ch_versions                // channel: [ path(versions.yml) ]
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

def kbQuantMqcHeader() {
    return [
        "# id: 'kb_quant'",
        "# section_name: 'Quantification (kallisto|bustools)'",
        "# description: 'kb count statistics for the gene-expression (GEX) and guide (sgRNA) libraries: reads processed, pseudoalignment rate, barcodes on the whitelist, and the resulting matrix dimensions (GEX after the bustools cell filter).'",
        "# plot_type: 'table'",
        "# pconfig:",
        "#     id: 'kb_quant_table'",
        "#     title: 'Quantification statistics'",
        "# headers:",
        "#     gex_reads: { title: 'GEX reads', format: '{:,.0f}' }",
        "#     gex_pseudoaligned_pct: { title: 'GEX pseudoaligned %', suffix: '%', min: 0, max: 100, format: '{:,.1f}' }",
        "#     gex_reads_on_whitelist_pct: { title: 'GEX reads on-list %', suffix: '%', min: 0, max: 100, format: '{:,.1f}' }",
        "#     gex_cells: { title: 'GEX cells (filtered)', format: '{:,.0f}' }",
        "#     gex_genes: { title: 'Genes', format: '{:,.0f}' }",
        "#     gex_median_umis_per_barcode: { title: 'GEX median UMIs/barcode', format: '{:,.0f}' }",
        "#     guide_reads: { title: 'Guide reads', format: '{:,.0f}' }",
        "#     guide_pseudoaligned_pct: { title: 'Guide pseudoaligned %', suffix: '%', min: 0, max: 100, format: '{:,.1f}' }",
        "#     guide_barcodes: { title: 'Guide barcodes', format: '{:,.0f}' }",
        "#     guide_features: { title: 'Guide features', format: '{:,.0f}' }",
        "#     guide_cells_with_reads: { title: 'GEX cells with guide reads', format: '{:,.0f}' }",
        "Sample\tgex_reads\tgex_pseudoaligned_pct\tgex_reads_on_whitelist_pct\tgex_cells\tgex_genes\tgex_median_umis_per_barcode\tguide_reads\tguide_pseudoaligned_pct\tguide_barcodes\tguide_features\tguide_cells_with_reads",
    ]
}

def kbQuantMqcHeaderLines() { return kbQuantMqcHeader().size() }

def kbQuantMqc(meta, gex_dir, dims, guide_dir, gstats) {
    def slurper = new groovy.json.JsonSlurper()
    def gri = slurper.parse(file("${gex_dir}/run_info.json"))
    def gin = slurper.parse(file("${gex_dir}/inspect.json"))
    def uri = slurper.parse(file("${guide_dir}/run_info.json"))
    def row = [ meta.id, gri.n_processed, gri.p_pseudoaligned, gin.percentageReadsOnOnlist, dims.cells, dims.genes, gin.medianUMIsPerBarcode,
                uri.n_processed, uri.p_pseudoaligned, gstats.barcodes, gstats.features, gstats.cells_with_guides ]
    return (kbQuantMqcHeader() + [ row.join('\t') ]).join('\n') + '\n'
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
