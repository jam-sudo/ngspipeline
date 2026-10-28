# jam-sudo/ngspipeline: Usage

> _Documentation of pipeline parameters is generated automatically from the pipeline schema; run `nextflow run jam-sudo/ngspipeline -r <version> --help` (or `--help_full`) to list them._

## Introduction

The pipeline takes 10x Genomics 3' Perturb-seq samples, each with a gene-expression (GEX) library and an sgRNA feature-barcode (guide) library, and writes count matrices, per-cell guide assignments and one ALIVE-ready `.h5ad` per sample. A run needs four inputs:

- `--input`: a samplesheet listing the FASTQ files of every sample ([below](#samplesheet-input))
- `--guides`: the guide library ([below](#guide-library))
- a reference: `--fasta` + `--gtf`, or a prebuilt `--reference_index` ([below](#reference))
- `--chemistry`: `10XV2` or `10XV3`, taken from the dataset's protocol

## Samplesheet input

Pass a comma-separated file with a header row and these six columns:

```bash
--input '[path to samplesheet file]'
```

| Column           | Required            | Description                                                                                         |
| ---------------- | ------------------- | --------------------------------------------------------------------------------------------------- |
| `sample_id`      | yes                 | Sample name without spaces. Rows with the same `sample_id` are merged into one sample.              |
| `gex_r1`         | yes                 | GEX library read 1 (cell barcode + UMI), `.fastq.gz` or `.fq.gz`.                                   |
| `gex_r2`         | yes                 | GEX library read 2 (cDNA).                                                                          |
| `guide_r1`       | on at least one row | Guide library read 1 (cell barcode + UMI).                                                          |
| `guide_r2`       | on at least one row | Guide library read 2 (protospacer read).                                                            |
| `expected_cells` | yes                 | Positive integer, identical on every row of a sample. Used only to report the called-cell fraction. |

Rules checked at start-up:

- Every sample needs at least one guide-read pair across its rows. Give `guide_r1` and `guide_r2` together or leave both blank.
- File paths and sample IDs cannot contain spaces. Relative paths are resolved against the samplesheet's directory.

### Multiple runs of the same sample

Give one row per sequencing run with the same `sample_id`. GEX pairs are taken from every row and guide pairs from the rows that carry them; the runs are counted together. Example with two GEX runs and one guide run:

```csv title="samplesheet.csv"
sample_id,gex_r1,gex_r2,guide_r1,guide_r2,expected_cells
sampleA,run1_gex_R1.fastq.gz,run1_gex_R2.fastq.gz,run1_guide_R1.fastq.gz,run1_guide_R2.fastq.gz,5000
sampleA,run2_gex_R1.fastq.gz,run2_gex_R2.fastq.gz,,,5000
```

Each `sample_id` is processed as its own sample (one GEM group). To also write one h5ad that contains every sample, add `pool_alive: true` to a `-params-file`; all samples must share the same reference.

An [example samplesheet](../assets/samplesheet.csv) and the [test samplesheet](../assets/samplesheet_test.csv) are provided with the pipeline.

## Guide library

`--guides` is a CSV with one row per sgRNA:

```csv title="guide_library.csv"
guide_id,target_gene,protospacer,vector_id
GENE1_sgA,GENE1,ACGTACGTACGTACGTACGT,GENE1_v1
GENE1_sgB,GENE1,TGCATGCATGCATGCATGCA,GENE1_v1
NT_0001,non-targeting,GATTACAGATTACAGATTAC,NT_0001
```

- `protospacer` is the 20-nt targeting sequence as it appears in the guide read.
- `vector_id` (optional) groups the sgRNAs of one vector, for example in dual-guide libraries; assignment is made per vector. Without it, each sgRNA is its own vector.
- Non-targeting controls must have `target_gene` = `non-targeting`; this is the control label in the ALIVE h5ad.

## Reference

Choose one:

- `--fasta` + `--gtf`: the pipeline builds the kallisto index with `kb ref` (`reference/kb_index/`). Building a full human genome index needs a lot of memory.
- `--reference_index <dir>`: a directory with a prebuilt kallisto index (`*.idx`) and `t2g.txt`. Use it for full human references on small machines. `bin/build_reference_index.sh <cdna.fa.gz> <ncrna.fa.gz> <outdir> [threads]` builds one from Ensembl cDNA and ncRNA FASTA with the same kallisto version the pipeline uses (needs Docker).

## Running the pipeline

The typical command for running the pipeline is as follows:

```bash
nextflow run jam-sudo/ngspipeline -r <version> -profile docker \
    --input samplesheet.csv --guides guide_library.csv \
    --reference_index /path/to/kb_index --chemistry 10XV3 \
    --outdir ./results
```

This will launch the pipeline with the `docker` configuration profile. See below for more information about profiles.

> [!NOTE]
> Numeric and boolean parameters given as `--name value` on the command line (`--min_ratio 3`, `--pool_alive true`) are parsed as strings and rejected by the parameter validation. Put them in a `-params-file`, or pass a boolean as a bare flag (`--pool_alive`).

Note that the pipeline will create the following files in your working directory:

```bash
work                # Directory containing the nextflow working files
<OUTDIR>            # Finished results in specified location (defined with --outdir)
.nextflow_log       # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```

If you wish to repeatedly use the same parameters for multiple runs, rather than specifying each flag in the command, you can specify these in a params file.

Pipeline settings can be provided in a `yaml` or `json` file via `-params-file <file>`.

> [!WARNING]
> Do not use `-c <file>` to specify parameters as this will result in errors. Custom config files specified with `-c` must only be used for [tuning process resource specifications](https://nf-co.re/docs/running/run-pipelines#configuring-pipelines), other infrastructural tweaks (such as output directories), or module arguments (args).

The above pipeline run specified with a params file in yaml format:

```bash
nextflow run jam-sudo/ngspipeline -r <version> -profile docker -params-file params.yaml
```

with:

```yaml title="params.yaml"
input: "./samplesheet.csv"
guides: "./guide_library.csv"
reference_index: "/path/to/kb_index"
chemistry: "10XV3"
outdir: "./results/"
assign_method: "threshold" # or "mixture"
min_umi: 10
min_ratio: 3
```

You can also generate such `YAML`/`JSON` files via [nf-core/launch](https://nf-co.re/launch).

### Guide assignment

- `assign_method: threshold` (default): a cell is `single` when its top vector has at least `min_umi` UMIs (default 10) and at least `min_ratio` (default 3) times the UMIs of the second vector.
- `assign_method: mixture`: a per-vector Poisson/Gaussian mixture on log2 UMI counts, as in Replogle et al. 2022; a cell is `single` when exactly one vector has posterior > 0.5. Vectors with too few cells to fit fall back to `UMI >= min_umi`.

Cells that are not `single` (`multi`, `unassigned`, `no_guide_reads`) are left out of the ALIVE h5ad; `keep_nonsingle: true` keeps them for inspection with `gene` set to their status. Every barcode with guide reads is in `guides/<sample>/assignment.tsv` with its evidence columns; `no_guide_reads` marks GEX cells without any.

### Updating the pipeline

When you run the above command, Nextflow automatically pulls the pipeline code from GitHub and stores it as a cached version. When running the pipeline after this, it will always use the cached version if available - even if the pipeline has been updated since. To make sure that you're running the latest version of the pipeline, make sure that you regularly update the cached version of the pipeline:

```bash
nextflow pull jam-sudo/ngspipeline
```

### Reproducibility

It is a good idea to specify the pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since.

First, go to the [jam-sudo/ngspipeline releases page](https://github.com/jam-sudo/ngspipeline/releases) and find the latest pipeline version - numeric only (eg. `1.3.1`). Then specify this when running the pipeline with `-r` (one hyphen) - eg. `-r 1.3.1`. Of course, you can switch to another version by changing the number after the `-r` flag.

This version number will be logged in reports when you run the pipeline, so that you'll know what you used when you look back in the future. For example, at the bottom of the MultiQC reports.

To further assist in reproducibility, you can use share and reuse [parameter files](#running-the-pipeline) to repeat pipeline runs with the same settings without having to write out a command with every single parameter.

> [!TIP]
> If you wish to share such profile (such as upload as supplementary material for academic publications), make sure to NOT include cluster specific paths to files, nor institutional specific profiles.

## Core Nextflow arguments

> [!NOTE]
> These options are part of Nextflow and use a _single_ hyphen (pipeline parameters use a double-hyphen)

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments.

Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker, Singularity, Podman, Shifter, Charliecloud, Apptainer, Conda) - see below.

> [!IMPORTANT]
> We highly recommend the use of Docker or Singularity containers for full pipeline reproducibility, however when this is not possible, Conda is also supported.

The pipeline also dynamically loads configurations from [https://github.com/nf-core/configs](https://github.com/nf-core/configs) when it runs, making multiple config profiles for various institutional clusters available at run time. For more information and to check if your system is supported, please see the [nf-core/configs documentation](https://github.com/nf-core/configs#documentation).

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended, since it can lead to different results on different machines dependent on the computer environment.

- `test`
  - A profile with a complete configuration for automated testing
  - Includes links to test data so needs no other parameters
- `local`
  - Local executor capped at 8 CPUs and 16 GB, with per-process sizes that let QC and both counting steps run side by side
- `slurm`
  - SLURM executor; needs `--slurm_partition` (and `--slurm_account` if the site requires one). Use with `singularity` or `apptainer`
- `awsbatch`
  - AWS Batch executor; needs `--aws_queue` (set `--aws_region` as well). Configuration only, not tested on AWS
- `emulate_amd64`
  - Runs the amd64 containers explicitly under emulation, for Docker on Apple Silicon (`-profile test,docker,emulate_amd64`)
- `docker`
  - A generic configuration profile to be used with [Docker](https://docker.com/)
- `singularity`
  - A generic configuration profile to be used with [Singularity](https://sylabs.io/docs/)
- `podman`
  - A generic configuration profile to be used with [Podman](https://podman.io/)
- `shifter`
  - A generic configuration profile to be used with [Shifter](https://nersc.gitlab.io/development/shifter/how-to-use/)
- `charliecloud`
  - A generic configuration profile to be used with [Charliecloud](https://charliecloud.io/)
- `apptainer`
  - A generic configuration profile to be used with [Apptainer](https://apptainer.org/)
- `wave`
  - A generic configuration profile to enable [Wave](https://seqera.io/wave/) containers. Use together with one of the above (requires Nextflow `24.03.0-edge` or later).
- `conda`
  - A generic configuration profile to be used with [Conda](https://conda.io/docs/). Please only use Conda as a last resort i.e. when it's not possible to run the pipeline with Docker, Singularity, Podman, Shifter, Charliecloud, or Apptainer.

### `-resume`

Specify this when restarting a pipeline. Nextflow will use cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously. For input to be considered the same, not only the names must be identical but the files' contents as well. For more info about this parameter, see [this blog post](https://www.nextflow.io/blog/2019/demystifying-nextflow-resume.html).

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

### `-c`

Specify the path to a specific config file (this is a core Nextflow command). See the [nf-core website documentation](https://nf-co.re/usage/configuration) for more information.

## Custom configuration

### Resource requests

Whilst the default requirements set within the pipeline will hopefully work for most people and with most input data, you may find that you want to customise the compute resources that the pipeline requests. Each step in the pipeline has a default set of requirements for number of CPUs, memory and time. For most of the pipeline steps, if the job exits with any of the error codes specified [here](https://github.com/nf-core/rnaseq/blob/4c27ef5610c87db00c3c5a3eed10b1d161abf575/conf/base.config#L18) it will automatically be resubmitted with higher resources request (2 x original, then 3 x original). If it still fails after the third attempt then the pipeline execution is stopped.

To change the resource requests, please see the [max resources](https://nf-co.re/docs/running/configuration/nextflow-for-your-system#set-max-resources) and [customise process resources](https://nf-co.re/docs/running/configuration/nextflow-for-your-system#customize-process-resources) section of the nf-core website.

### Custom Containers

In some cases, you may wish to change the container or conda environment used by a pipeline steps for a particular tool. By default, nf-core pipelines use containers and software from the [biocontainers](https://biocontainers.pro/) or [bioconda](https://bioconda.github.io/) projects. However, in some cases the pipeline specified version maybe out of date.

To use a different container from the default container or conda environment specified in a pipeline, please see the [updating tool versions](https://nf-co.re/docs/running/configuration/nextflow-for-your-system#update-tool-versions) section of the nf-core website.

### Custom Tool Arguments

A pipeline might not always support every possible argument or option of a particular tool used in pipeline. Fortunately, nf-core pipelines provide some freedom to users to insert additional parameters that the pipeline does not include by default.

To learn how to provide additional arguments to a particular tool of the pipeline, please see the [customising tool arguments](https://nf-co.re/docs/running/configuration/nextflow-for-your-system#modifying-tool-arguments) section of the nf-core website.

### nf-core/configs

In most cases, you will only need to create a custom config as a one-off but if you and others within your organisation are likely to be running nf-core pipelines regularly and need to use the same settings regularly it may be a good idea to request that your custom config file is uploaded to the `nf-core/configs` git repository. Before you do this please can you test that the config file works with your pipeline of choice using the `-c` parameter. You can then create a pull request to the `nf-core/configs` repository with the addition of your config file, associated documentation file (see examples in [`nf-core/configs/docs`](https://github.com/nf-core/configs/tree/master/docs)), and amending [`nfcore_custom.config`](https://github.com/nf-core/configs/blob/master/nfcore_custom.config) to include your custom profile.

See the main [Nextflow documentation](https://www.nextflow.io/docs/latest/config.html) for more information about creating your own configuration files.

If you have any questions or issues please send us a message on [Slack](https://nf-co.re/join/slack) on the [`#configs` channel](https://nfcore.slack.com/channels/configs).

## Running in the background

Nextflow handles job submissions and supervises the running jobs. The Nextflow process must run until the pipeline is finished.

The Nextflow `-bg` flag launches Nextflow in the background, detached from your terminal so that the workflow does not stop if you log out of your session. The logs are saved to a file.

Alternatively, you can use `screen` / `tmux` or similar tool to create a detached session which you can log back into at a later time.
Some HPC setups also allow you to run nextflow within a cluster job submitted your job scheduler (from where it submits more jobs).

## Nextflow memory requirements

In some cases, the Nextflow Java virtual machines can start to request a large amount of memory.
We recommend adding the following line to your environment to limit this (typically in `~/.bashrc` or `~./bash_profile`):

```bash
NXF_OPTS='-Xms1g -Xmx4g'
```
