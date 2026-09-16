# 06 — T-30 runbook: full lane_4 run on Discovery (`-profile slurm,singularity`)

Human-executed (CLAUDE.md rule 9 applies to AWS; Discovery is free but still the human's account). Goal: the same h5ad sha256 as the local run in `docs/03_cross_profile_hashes.md`, which requires the **same parameters as T-16**: `assign_params.yml` with `min_umi: 5`, `min_ratio: 3`, `assign_method: threshold`, `--chemistry 10XV3`, the same prebuilt index and guide library.

Values marked NEEDS_HUMAN are cluster facts the agent must not guess (CLAUDE.md rule 1); read them from the cluster with the commands shown.

## 0. Facts to read off the cluster first

```bash
ssh <user>@login.discovery.neu.edu
sinfo -s                      # partition names and time limits → --slurm_partition
sacctmgr show assoc user=$USER format=account,partition,qos   # account / QOS, if any → --slurm_account / --slurm_extra
module avail 2>&1 | grep -i -E "nextflow|java|jdk|singularity|apptainer"
echo $SCRATCH; ls -d /scratch/$USER 2>/dev/null    # scratch path for work dir + SIF cache
singularity --version || apptainer --version
```

## 1. Copy inputs (from the MacBook)

```bash
D=<user>@xfer.discovery.neu.edu:/scratch/<user>/ngs      # NEEDS_HUMAN: transfer host / scratch path
rsync -avP ~/ngs_data/replogle_k562_essential_lane4/*.fastq.gz ~/ngs_data/replogle_k562_essential_lane4/md5sums.txt $D/fastq/
rsync -avP ~/ngs_ref/kallisto_cdna_GRCh38_ens116/ $D/kallisto_cdna_GRCh38_ens116/
rsync -avP ~/ngs_data/replogle_library/K562_day6_essential_guide_library.csv ~/ngs_data/runs/assign_params.yml $D/
sed 's#/Users/jam/ngs_data/replogle_k562_essential_lane4#/scratch/<user>/ngs/fastq#g' ~/ngs_data/runs/samplesheet_lane4.csv > /tmp/samplesheet_lane4_discovery.csv
rsync -avP /tmp/samplesheet_lane4_discovery.csv $D/
```

On the cluster: `cd /scratch/<user>/ngs/fastq && md5sum -c md5sums.txt` (24 files OK).

## 2. Nextflow + pipeline on the cluster

```bash
module load <java module from step 0>          # Java 17+ ; or module load nextflow if it exists
curl -s https://get.nextflow.io | bash && mkdir -p ~/bin && mv nextflow ~/bin/ && export PATH=~/bin:$PATH
nextflow -version
git clone -b dev https://github.com/jam-sudo/ngspipeline.git /scratch/<user>/ngspipeline
export NXF_SINGULARITY_CACHEDIR=/scratch/<user>/sif_cache; mkdir -p $NXF_SINGULARITY_CACHEDIR
```

## 3. Smoke test on the cluster (F3 on SLURM, minutes)

Run the head process inside `tmux` on the login node (it only submits jobs and pulls images; compute goes to SLURM):

```bash
tmux new -s nf
cd /scratch/<user>/ngspipeline
nextflow run . -profile test,slurm,singularity --slurm_partition <partition> [--slurm_account <acct>] \
  --outdir /scratch/<user>/runs/test -work-dir /scratch/<user>/work_test
```

Expect `Pipeline completed successfully`, 9 processes. If image pulls fail on compute nodes, the pull happens on the login node anyway (Nextflow pulls before submitting), so check `$NXF_SINGULARITY_CACHEDIR`.

## 4. Full sample

```bash
nextflow run . -profile slurm,singularity --slurm_partition <partition> [--slurm_account <acct>] \
  --input /scratch/<user>/ngs/samplesheet_lane4_discovery.csv \
  --guides /scratch/<user>/ngs/K562_day6_essential_guide_library.csv \
  --reference_index /scratch/<user>/ngs/kallisto_cdna_GRCh38_ens116 --chemistry 10XV3 \
  -params-file /scratch/<user>/ngs/assign_params.yml \
  --outdir /scratch/<user>/runs/lane4_slurm -work-dir /scratch/<user>/work_lane4 -resume
```

Detach with `Ctrl-b d`; reattach with `tmux attach -t nf`. Local reference: kb count ≈ 21 min / 15.9 GB RSS, whole run ≈ 50 min of compute; on a partition with a 24 h limit this is comfortable. If the head process dies (login-node limits), rerun the same command with `-resume`.

## 5. Evidence to bring back

```bash
cd /scratch/<user>/runs/lane4_slurm
sha256sum alive/replogle_k562_essential_lane4.h5ad          # compare with docs/03 local value 305e31d1…
ls pipeline_info/                                            # execution_trace_*.txt, execution_report_*.html, execution_timeline_*.html
grep -E "KALLISTOBUSTOOLS_COUNT|GUIDE_COUNT" pipeline_info/execution_trace_*.txt | cut -f4,5,9,10,11
```

Copy `pipeline_info/` and the sha256 line back (`rsync -avP <user>@xfer.discovery.neu.edu:/scratch/<user>/runs/lane4_slurm/pipeline_info ~/ngs_data/runs/lane4_slurm_pipeline_info`) and hand them to the agent: it fills `docs/03_cross_profile_hashes.md`, the README run-statistics slurm row (wall time, peak RSS, $0) and `docs/progress.md` T-30/F7. If the hash differs, keep the h5ad: the numeric `obs`/`var`/`X` comparison described in docs/03 is done next.

## 6. Cleanup

`rm -rf /scratch/<user>/work_lane4 /scratch/<user>/work_test` after the evidence is copied; scratch is not backed up, so keep `results/alive/*.h5ad` until docs/03 is updated.
