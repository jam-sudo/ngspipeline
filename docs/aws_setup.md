> **Not executed.** AWS Batch execution was waived on 2026-09-16 (docs/decisions/010-aws-waiver.md). This document and `conf/awsbatch.config` are configuration-only deliverables and have not been tested against a real AWS account.

# AWS Batch setup (T-31) — configuration only; the human creates the resources and launches runs

Budget guard: PLAN.md caps the whole exercise at **$100**; billing alarms at $50/$100 are a T-03 deliverable (`docs/aws_budget.png`). CLAUDE.md rule 9: the agent never runs anything that costs money.

## 1. Region and bucket

- Region: choose one close to the data and stay in it (`--aws_region`, e.g. `us-east-1`). Record it here once chosen: `AWS_REGION = NEEDS_HUMAN`.
- S3 bucket: `s3://<bucket>` with two prefixes: `work/` (Nextflow work dir, deleted after the run) and `results/` (`--outdir`). Enable default encryption; no public access.

## 2. IAM (least privilege)

Create a user or role for launching Nextflow with this policy (replace `<bucket>` and `<region>`); the Batch compute environment uses the AWS-managed `AWSBatchServiceRole` and an ECS instance role with S3 access to the same bucket.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Work",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": ["arn:aws:s3:::<bucket>", "arn:aws:s3:::<bucket>/*"]
    },
    {
      "Sid": "Batch",
      "Effect": "Allow",
      "Action": [
        "batch:SubmitJob",
        "batch:DescribeJobs",
        "batch:TerminateJob",
        "batch:DescribeJobQueues",
        "batch:DescribeJobDefinitions",
        "batch:RegisterJobDefinition",
        "batch:DescribeComputeEnvironments"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Logs",
      "Effect": "Allow",
      "Action": ["logs:GetLogEvents", "logs:DescribeLogStreams"],
      "Resource": "arn:aws:logs:<region>:*:log-group:/aws/batch/job:*"
    }
  ]
}
```

## 3. Compute environment and job queue

- Managed compute environment, **Spot** (cheaper; kb count is restartable via `-resume`), instance types `optimal` or `m5/r5` family, min vCPUs 0, max vCPUs 32, allocation strategy `SPOT_CAPACITY_OPTIMIZED`.
- AMI: an ECS-optimised AMI with the AWS CLI available at `--aws_cli` (default `/home/ec2-user/miniconda/bin/aws`, the nf-core/Nextflow convention) **or** use Fusion/Wave (then `aws_cli` is ignored). Root volume ≥ 100 GB (kb work dirs for a 15 GB sample reach ~40 GB).
- Job queue `ngspipeline-spot` (`--aws_queue`) attached to the compute environment.
- Memory: the largest task (kb count, prebuilt index) peaked at 15.9 GB on the MacBook (T-16); `conf/awsbatch.config` caps at 64 GB / 16 vCPU.

## 4. Run (human)

```bash
nextflow run jam-sudo/ngspipeline -r <sha> -profile awsbatch,docker \
  --input samplesheet_lane4.csv --guides s3://<bucket>/ref/K562_day6_essential_guide_library.csv \
  --reference_index s3://<bucket>/ref/kb_GRCh38_ens116 --chemistry 10XV3 -params-file assign_params.yml \
  --aws_queue ngspipeline-spot --aws_region <region> \
  -work-dir s3://<bucket>/work --outdir s3://<bucket>/results/lane4
```

Inputs (FASTQ, index, library) must be uploaded to the bucket first (~17 GB). Expected duration on 16 vCPU: kb count ~10–20 min, FastQC ~20 min (parallel), rest < 10 min.

## 5. After the run (DoD, PLAN.md T-31)

1. `aws s3 cp s3://<bucket>/results/lane4/alive/replogle_k562_essential_lane4.h5ad - | sha256sum` → `docs/03_cross_profile_hashes.md`.
2. Cost Explorer screenshot; total must stay under $100.
3. Disable the compute environment (`aws batch update-compute-environment --state DISABLED`), delete `s3://<bucket>/work` (`aws s3 rm --recursive`), confirm both in progress.md.
