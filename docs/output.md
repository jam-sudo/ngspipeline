# jam-sudo/ngspipeline: Output

## Introduction

This document describes the output produced by the pipeline. The directories listed below will be created in the results directory (`--outdir`) after the pipeline has finished. All paths are relative to the top-level results directory; `<sample>` is the samplesheet `sample_id`.

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes data using the following steps:

- [FastQC](#fastqc) - raw read QC of the GEX and guide libraries
- [GEX quantification](#gex-quantification) - kallisto|bustools count matrices and cell calling
- [Guide counting and assignment](#guide-counting-and-assignment) - kb kite guide counts and the per-cell vector assignment
- [ALIVE h5ad](#alive-h5ad) - the analysis-ready AnnData file per sample (and pooled)
- [Reference indices](#reference-indices) - indices built during the run
- [MultiQC](#multiqc) - aggregate report describing results and QC from the whole pipeline
- [Pipeline information](#pipeline-information) - report metrics generated during the workflow execution

### FastQC

<details markdown="1">
<summary>Output files</summary>

- `fastqc/`
  - `<sample>_gex_{1,2}_fastqc.html`, `<sample>_guide_{1,2}_fastqc.html`: FastQC report per read of each library.
  - `*_fastqc.zip`: zip archive containing the FastQC report, tab-delimited data file and plot images.

</details>

[FastQC](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/) gives general quality metrics about your sequenced reads. It provides information about the quality score distribution across your reads, per base sequence content (%A/T/G/C), adapter contamination and overrepresented sequences. For further reading and documentation see the [FastQC help pages](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/).

### GEX quantification

<details markdown="1">
<summary>Output files</summary>

- `counts/<sample>/`: the native `kb count` output directory, unchanged.
  - `counts_unfiltered/cells_x_genes.{mtx,barcodes.txt,genes.txt,genes.names.txt}`: all whitelisted barcodes × genes.
  - `counts_filtered/cells_x_genes.{mtx,barcodes.txt,genes.txt,genes.names.txt}`: cells kept by the bustools knee filter (`--filter bustools`). These are the cells used downstream.
  - `filter_barcodes.txt`: barcodes that passed the filter.
  - `output.bus`, `output.unfiltered.bus`, `output.filtered.bus`, `matrix.ec`, `transcripts.txt`: BUS files and equivalence classes.
  - `run_info.json`, `inspect.json`, `kb_info.json`: pseudoalignment and barcode statistics (pseudoaligned fraction, reads on the whitelist).
  - `10x_version{2,3}_whitelist.txt`: the cell-barcode whitelist of `--chemistry`.

</details>

GEX reads are pseudoaligned with [kallisto|bustools](https://www.kallistobus.tools/). `matrix.ec` is not byte-stable between runs; the count matrices are.

### Guide counting and assignment

<details markdown="1">
<summary>Output files</summary>

- `guides/<sample>/`
  - `counts_unfiltered/cells_x_features.{mtx,barcodes.txt,genes.txt,genes.names.txt}` and `counts_unfiltered/adata.h5ad`: `kb count` kite output, all barcodes × sgRNAs.
  - `guide_counts.h5ad`: a copy of `counts_unfiltered/adata.h5ad` (guide UMI matrix, all barcodes × sgRNAs).
  - `10x_feature_barcode_map.txt`, `10x_fb_whitelist.txt`: the `kite:10xFB` map that translates feature-barcode reads to the GEX barcode, and its whitelist.
  - `output.bus`, `output.unfiltered.bus`, `matrix.ec`, `transcripts.txt`, `run_info.json`, `inspect.json`, `kb_info.json`: kb kite intermediates and statistics.
  - `assignment.tsv`: one row per GEX-called cell (`counts_filtered/`) found in the guide matrix. Columns: `cell_barcode`, `guide_id` (assigned vector; `sgID_A|sgID_B` for dual-guide vectors), `target_gene`, `method`, `top1_umi`, `top2_umi`, `ratio`, `posterior` (mixture only), `status` (`single` / `multi` / `unassigned`), `top1_guide_id`, `top2_guide_id`, `n_assigned`, `total_guide_umi`.
  - `assignment_summary.tsv`: method, number of cells and vectors, and the count per status (with `mixture`, also the number of fitted and fallback vectors).
  - `<sample>_guide_assignment_mqc.tsv`, `<sample>_guide_assignment_generalstats_mqc.tsv`: tables for the MultiQC guide-assignment section.

</details>

Guide UMIs are summed per vector (`vector_id` of the guide library). With `--assign_method threshold`, a cell is `single` when the top vector has at least `min_umi` UMIs and at least `min_ratio` times the UMIs of the second vector; with `mixture`, when exactly one vector has posterior > 0.5. See [usage](usage.md#guide-assignment).

### ALIVE h5ad

<details markdown="1">
<summary>Output files</summary>

- `alive/`
  - `<sample>.h5ad`: raw GEX UMI counts (CSR, integer-valued) of the `single` cells, with the assignment in `obs` (`gene` is the perturbation label, `non-targeting` for controls).
  - `pooled.h5ad`: with `pool_alive: true` and more than one sample, every sample in one file; the obs index is `<cell_barcode>-<sample_id>`.
  - `<sample>.alive_summary.json`, `pooled.alive_summary.json`: cells written, control cells, genes, number of perturbation labels and status counts.

</details>

The exact `obs`, `var` and `uns` layout is in [`alive_schema.md`](alive_schema.md); `bin/check_alive_schema.py <h5ad>` checks a file against it. Cells that are not `single` are excluded unless `keep_nonsingle: true`.

### Reference indices

<details markdown="1">
<summary>Output files</summary>

- `reference/kb_index/`: `kb_ref_out.idx` and `t2g.txt`, only when the index is built from `--fasta`/`--gtf`.
- `reference/guide_index/`: `kite.idx`, `t2g.txt`, `features.tsv`, `feature_map.tsv` and `mismatch.fa` (the protospacers with their Hamming-1 variants).

</details>

Reuse `reference/kb_index/` as `--reference_index` in later runs to skip the index build.

### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

[MultiQC](http://multiqc.info) is a visualization tool that generates a single HTML report summarising all samples in your project. The report has FastQC, a kb quantification table (pseudoaligned reads, cells called) and the guide-assignment status of every sample. The pipeline also reports the software versions and a methods description for traceability. For more information about how to use MultiQC reports, see <http://multiqc.info>.

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report_<date>.html`, `execution_timeline_<date>.html`, `execution_trace_<date>.txt` and `pipeline_dag_<date>.html`.
  - Parameters used by the pipeline run: `params_<date>.json`.
  - Software versions of every process: `ngspipeline_software_mqc_versions.yml`.

</details>

[Nextflow](https://docs.seqera.io/platform-cloud/reports/overview) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.
