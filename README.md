# jam-sudo/ngspipeline

[![GitHub Actions CI Status](https://github.com/jam-sudo/ngspipeline/actions/workflows/nf-test.yml/badge.svg)](https://github.com/jam-sudo/ngspipeline/actions/workflows/nf-test.yml)
[![GitHub Actions Linting Status](https://github.com/jam-sudo/ngspipeline/actions/workflows/linting.yml/badge.svg)](https://github.com/jam-sudo/ngspipeline/actions/workflows/linting.yml)[![nf-test](https://img.shields.io/badge/unit_tests-nf--test-337ab7.svg)](https://www.nf-test.com)

[![Nextflow](https://img.shields.io/badge/version-%E2%89%A525.10.4-green?style=flat&logo=nextflow&logoColor=white&color=%230DC09D&link=https%3A%2F%2Fnextflow.io)](https://www.nextflow.io/)
[![nf-core template version](https://img.shields.io/badge/nf--core_template-4.1.0-green?style=flat&logo=nfcore&logoColor=white&color=%2324B064&link=https%3A%2F%2Fnf-co.re)](https://github.com/nf-core/tools/releases/tag/4.1.0)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)
[![GitHub release](https://img.shields.io/github/v/release/jam-sudo/ngspipeline)](https://github.com/jam-sudo/ngspipeline/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Launch on Seqera Platform](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Seqera%20Platform-%234256e7)](https://cloud.seqera.io/launch?pipeline=https://github.com/jam-sudo/ngspipeline)

## Introduction

**Latest release: tag [`1.0.2`](https://github.com/jam-sudo/ngspipeline/releases/tag/1.0.2)** (run it with `-r 1.0.2`); development continues on `dev`.

**jam-sudo/ngspipeline** turns raw Perturb-seq reads into an analysis-ready dataset for [ALIVE](https://github.com/jam-sudo/alive): FASTQ → gene-expression (GEX) and sgRNA count matrices → per-cell guide assignment → an ALIVE-ready `.h5ad`. It is a Nextflow DSL2 pipeline built on the nf-core template and nf-core modules; the four steps that have no nf-core module are hand-written local modules.

```mermaid
flowchart LR
    subgraph inputs
        SS[samplesheet.csv<br/>GEX + guide FASTQ per run]
        GL[guide_library.csv]
        REF[--fasta + --gtf<br/>or --reference_index]
    end
    SS --> FQ[FASTQC<br/>nf-core]
    REF --> KBR[KALLISTOBUSTOOLS_REF<br/>nf-core, kb ref]
    KBR --> KBC[KALLISTOBUSTOOLS_COUNT<br/>nf-core, kb count + bustools cell filter]
    SS --> KBC
    GL --> GI[GUIDE_INDEX<br/>local, kb ref --workflow kite]
    GI --> GC[GUIDE_COUNT<br/>local, kb count kite:10xFB]
    SS --> GC
    KBC --> GA[GUIDE_ASSIGN<br/>local, threshold or mixture]
    GC --> GA
    KBC --> H5[TO_ALIVE_H5AD<br/>local]
    GA --> H5
    FQ --> MQ[MULTIQC<br/>nf-core + custom content]
    KBC --> MQ
    GC --> MQ
    GA --> MQ
    H5 --> OUT[(alive/&lt;sample&gt;.h5ad)]
```

1. Read QC of both libraries ([`FastQC`](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/)).
2. GEX quantification with [kallisto|bustools](https://www.kallistobus.tools/) (`kb ref` on `--fasta`/`--gtf`, or a prebuilt `--reference_index`; `kb count --filter bustools` for empty-droplet removal). Native kb output is kept as-is.
3. Guide counting with the kb **kite** workflow: protospacers indexed with Hamming-1 variants, `kite:10xFB` translates the 10x 3' v3 feature-barcode variant to the GEX barcode.
4. Per-cell guide (vector) assignment, `--assign_method threshold` or `mixture` (Poisson/Gaussian on log2 UMI, Replogle et al.), with every evidence column in `assignment.tsv`.
5. `alive/<sample>.h5ad`: raw counts + assignment; non-single cells excluded by default (schema in [`docs/alive_schema.md`](docs/alive_schema.md)).
6. One [MultiQC](https://multiqc.info/) report with FastQC, quantification statistics and the guide-assignment section.

## Usage

This section is a quick start. The full input reference and options are in [`docs/usage.md`](docs/usage.md), every output file is described in [`docs/output.md`](docs/output.md), and `--help` lists all parameters.

### Setup and first run

Use Nextflow **25.10.4 or newer** and a working Docker or Singularity runtime. The bundled test profile caps each task at 4 CPUs and 10 GB RAM. GEX and guide counting can run concurrently, so allow memory for both tasks. For the development MacBook E2E run, use Colima with 8 CPUs, 20 GB RAM and Rosetta:

```bash
colima start --cpu 8 --memory 20 --vz-rosetta
docker info
```

Run the released pipeline on the bundled real-read test data before using your own inputs:

```bash
NXF_VER=25.10.4 nextflow run jam-sudo/ngspipeline -r 1.0.2 \
  -profile test,docker --outdir results/test
```

On Apple Silicon, add `emulate_amd64` to the profiles (`test,docker,emulate_amd64`) to explicitly select the amd64 containers. For a local checkout, replace `jam-sudo/ngspipeline -r 1.0.2` with `.`; this runs the checked-out code, including development changes. Keep the work directory under your home directory when using Colima so containers can access it.

### Inputs

`samplesheet.csv` — one row per sequencing run; rows with the same `sample_id` are merged (GEX pairs from every row, guide pairs from the rows that carry them). Relative paths are resolved against the samplesheet's directory.

```csv
sample_id,gex_r1,gex_r2,guide_r1,guide_r2,expected_cells
sampleA,run1_gex_R1.fastq.gz,run1_gex_R2.fastq.gz,run1_guide_R1.fastq.gz,run1_guide_R2.fastq.gz,3681
sampleA,run2_gex_R1.fastq.gz,run2_gex_R2.fastq.gz,,,3681
```

`guide_library.csv` — one row per sgRNA: `guide_id,target_gene,protospacer[,vector_id]`. `vector_id` groups the sgRNAs of one vector (dual-guide libraries); non-targeting controls have `target_gene` = `non-targeting`.

Every sample needs paired GEX reads and at least one guide-read pair across its rows. Supply both guide paths together or leave both blank. `expected_cells` must be a positive integer and agree across rows of the same sample. FASTQ paths and sample IDs cannot contain spaces. Example inputs: [`assets/samplesheet_test.csv`](assets/samplesheet_test.csv), [`assets/guide_library_test.csv`](assets/guide_library_test.csv).

Reference: `--fasta` + `--gtf` (the pipeline builds the kb index) or `--reference_index <dir>` containing `*.idx` and `t2g.txt` (build a prebuilt cDNA index with `bin/build_reference_index.sh`; use it for the full human reference on small machines).

`--chemistry` (`10XV2` | `10XV3`) selects the 10x whitelist and read layout and must be set from the dataset's protocol. `--min_umi` defaults to 10 and `--min_ratio` to 3; override them with `-params-file` (see the note below).

Main parameters:

| parameter                                  | default     | meaning                                                                                                                            |
| ------------------------------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `--input`, `--guides`, `--outdir`          | required    | samplesheet, guide library, output directory                                                                                       |
| `--chemistry`                              | required    | `10XV2` or `10XV3`                                                                                                                 |
| `--reference_index` or `--fasta` + `--gtf` | required    | prebuilt kb index directory, or genome + annotation to build one                                                                   |
| `--kb_workflow`                            | `standard`  | kb workflow for GEX (`standard` or `nac`)                                                                                          |
| `--assign_method`                          | `threshold` | `threshold` (top-1 UMI ≥ `min_umi` and top-1/top-2 ≥ `min_ratio`) or `mixture` (per-vector Poisson/Gaussian, Replogle et al. 2022) |
| `--min_umi`, `--min_ratio`                 | `10`, `3`   | assignment thresholds; `min_umi` is also the fallback for vectors the mixture cannot fit                                           |
| `--keep_nonsingle`                         | `false`     | keep `multi` / `unassigned` cells in the h5ad (label = status) for inspection                                                      |
| `--pool_alive`                             | `false`     | also write `alive/pooled.h5ad` across all samples (one shared reference)                                                           |
| `--slurm_partition`, `--slurm_account`     | —           | required by `-profile slurm` (account only if the site needs it)                                                                   |

### Run

```bash
NXF_VER=25.10.4 nextflow run jam-sudo/ngspipeline -r 1.0.2 -profile docker,local \
   --input samplesheet.csv --guides guide_library.csv \
   --reference_index /path/to/kb_index --chemistry 10XV3 \
   -params-file assign_params.yml \
   --outdir <OUTDIR>
```

`assign_params.yml` (only needed to override the defaults):

```yaml
assign_method: threshold
min_umi: 10
min_ratio: 3
```

> [!NOTE]
> Numeric and boolean parameters given as `--name value` on the command line (`--min_ratio 3`, `--pool_alive true`) are rejected by the parameter validation (parsed as strings); put them in a `-params-file` (`pool_alive: true`) or, for booleans, pass the bare flag `--pool_alive`.

> [!WARNING]
> Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_; see [docs](https://nf-co.re/docs/usage/getting_started/configuration#custom-configuration-files).

Test profile (18 MB subsample of a real Perturb-seq sample, see [`assets/test_data/README.md`](assets/test_data/README.md)). From the repository root:

```bash
NXF_VER=25.10.4 nextflow run . -profile test,docker --outdir results/test
```

This executes FASTQ QC, both reference builds, GEX and guide counting, guide assignment, h5ad export and MultiQC. The test profile uses `min_umi: 5`, `min_ratio: 3`; production defaults are `min_umi: 10`, `min_ratio: 3`. Add `-resume` when restarting an interrupted run with the same work directory.

### Outputs (`--outdir`)

File-by-file descriptions are in [`docs/output.md`](docs/output.md).

```
fastqc/                              read QC reports for both libraries
counts/<sample>/                      kb count native output (counts_unfiltered/, counts_filtered/, *.bus, run_info.json, ...)
guides/<sample>/guide_counts.h5ad     cells x guides (all barcodes; kite)
guides/<sample>/assignment.tsv        cell_barcode, guide_id, target_gene, method, top1_umi, top2_umi, ratio, posterior, status{single,multi,unassigned}, ...
guides/<sample>/assignment_summary.tsv
alive/<sample>.h5ad                   counts + assignment (obs: cell_barcode, gene, guide_id, target_gene, assignment_status, assignment_confidence, assignment_method, ...)
alive/pooled.h5ad                     with --pool_alive and > 1 sample: all samples, obs index <barcode>-<sample_id>
alive/<id>.alive_summary.json         cells, labels, status counts per h5ad
reference/{kb_index,guide_index}/     indices built in-pipeline
multiqc/multiqc_report.html
pipeline_info/{execution_report,execution_timeline,execution_trace,pipeline_dag}
```

## Run statistics

Sample: Replogle 2022 K562 essential-scale, GEM group `lane_4` (235 M GEX read pairs, 19.7 M guide read pairs), prebuilt cDNA index, `--assign_method threshold`.

| profile                                        | host                                                | wall time                                                            | peak memory (process)                                   | notes                                               |
| ---------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------- |
| `local,docker`                                 | MacBook M5 Pro 24 GB, Colima 8 CPU / 20 GB, Rosetta | 2 h 23 min (≈ 50 min without an operator-interrupted FastQC attempt) | 15.9 GB (KALLISTOBUSTOOLS_COUNT)                        | Full lane_4                                         |
| `test,singularity`                             | Colima VM, Apptainer 1.5.3, aarch64 + Rosetta       | 2 min 35 s (Docker: 1 min 33 s)                                      | 8.8 GB (GUIDE_COUNT)                                    | Identical h5ad across test profiles                 |
| `slurm,singularity`                            | SLURM cluster, 28-core / 186 GB node                | 28 min 9 s                                                           | 35.7 GB (KALLISTOBUSTOOLS_COUNT)                        | Full lane_4; h5ad identical to local                |
| `slurm,singularity`, 12 lanes + `--pool_alive` | SLURM cluster, 12 samples in parallel               | 1 h 52 min                                                           | 36.2 GB (KALLISTOBUSTOOLS_COUNT), 10.1 GB (pooled h5ad) | 104,551 pooled cells; ALIVE prepare + fit completed |

The `awsbatch` profile is configured but has not been run on AWS.

## Validation

All checks use the Replogle 2022 K562 essential-scale data, compared with the authors' published per-cell guide identities. No threshold was changed after seeing these results.

- **Guide assignment.** On GEM group `lane_4`, all 3,681 cells in the authors' table are among the pipeline's filtered cells, and 96.0 % of them get the same vector (99.3 % of the cells the pipeline calls `single`). On all 12 GEM groups, run one sample per lane, the per-lane figure is 95.3–96.3 % (99.1–99.4 % of pipeline-`single` cells). These numbers use the threshold method with `min_umi 5`, `min_ratio 3`, the values in use before the defaults were set; they were not recomputed with the defaults.
- **Where the other ~4 % go.** Mostly cells the pipeline calls `multi` (two vectors above threshold) and cells whose top vector sits just below `min_umi`.
- **Mixture method.** 91.8 % on `lane_4` (99.4 % of `single` cells). It is lower because one GEM group has about 1.6 cells per vector, so the mixture could be fit for only 125 of 2,291 vectors (the rest fall back to `min_umi`); the authors fit each guide over the whole experiment.
- **Extra cells.** The bustools knee filter keeps about twice as many barcodes as the authors' table (7,132 vs 3,681 on `lane_4`). The extra cells have GEX and guide UMI depths similar to the authors' cells; they are kept, not filtered to match.
- **Defaults.** `min_umi 10` is the smallest round number above the 99th percentile (6 UMIs) of the top vector in empty droplets of `lane_4`; `min_ratio` stays 3. On `lane_4`, 752 of 7,132 cells fall below 10 (564 below 5), almost all of them absent from the authors' table.
- **Reproducibility.** The `lane_4` h5ad has the same sha256 from `local,docker`, from `slurm,singularity` and from inside the 12-sample SLURM run. The test-profile h5ad is identical across Docker, Apptainer and SLURM. The pipeline version is stored in `uns['provenance']`, so files from different releases differ in that field only.
- **`-resume`.** A test run killed during counting resumed with the 4 finished tasks cached and the 5 remaining tasks re-run.
- **ALIVE.** ALIVE `prepare` and `fit` ran on the 12-lane `pooled.h5ad` with no change to ALIVE's loader.

## Scope and limitations

- 10x Genomics 3' gene expression with a CRISPR feature-barcode (guide capture) library. Validated on `10XV3`, where `kite:10xFB` translates the feature-barcode variant to the GEX barcode. `10XV2` runs plain kite and has not been tested on real data.
- The 20-nt protospacer must be readable in guide read 2; assignment is per vector (`vector_id`), so dual-guide libraries are supported.
- Cells are the bustools knee-filter cells of the GEX library. No doublet removal or mitochondrial / gene-count QC is applied; only `single` cells go into the h5ad unless `--keep_nonsingle` is set.
- `--pool_alive` needs every sample to use the same reference.

## Development

### End-to-end validation

From the repository root, run the existing pipeline test with nf-test (CI pins nf-test 0.9.4). Use a fresh `NFT_WORKDIR` for a new execution; `--ci` prevents creating missing snapshots silently:

```bash
NXF_VER=25.10.4 NFT_WORKDIR=testing/e2e/nf-test \
  nf-test test tests/default.nf.test --profile test,docker --ci
```

On Apple Silicon use `--profile test,docker,emulate_amd64`. The test requires workflow success, 96–120 filtered GEX cells, 200 genes, 108 guide features, guide and ALIVE h5ad outputs, and matching snapshots of stable output paths and contents. It covers the single-sample threshold-assignment path with an in-pipeline reference build; pooled export and other assignment modes are covered separately by the local module tests.

Validate the final ALIVE schema using the existing checker (requires the Python environment with `anndata`, `numpy` and `scipy`):

```bash
python bin/check_alive_schema.py results/test/alive/replogle_k562_lane4_test.h5ad
```

Run all repository-owned tests, including the pipeline and local module tests:

```bash
NXF_VER=25.10.4 nf-test test . --profile test,docker --ci
```

Module tests live under `modules/local/*/tests`; the end-to-end pipeline test lives in `tests/`.

## Credits

jam-sudo/ngspipeline was written by Jae Min Yoon.

## Citations

Data used for testing and validation: Replogle et al. 2022, _Cell_ 185(14):2559–2575, [doi:10.1016/j.cell.2022.05.013](https://doi.org/10.1016/j.cell.2022.05.013) (SRA PRJNA831566; processed data CC BY 4.0).

An extensive list of references for the tools used by the pipeline can be found in the [`CITATIONS.md`](CITATIONS.md) file.

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [MIT license](https://github.com/nf-core/tools/blob/main/LICENSE).

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Matthias Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).
