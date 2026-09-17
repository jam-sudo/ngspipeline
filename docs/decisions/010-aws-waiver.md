# 010 — AWS Batch execution waived

Status: accepted (2026-09-16) — decided by the human ("aws는 안쓰려고하는데"), recorded by the agent under delegation
Task: T-31 (also T-03 AWS items, T-32 awsbatch row, F7, T-42 wording)

## Context

PLAN.md §1 F7 requires the full sample to complete on three profiles (local, slurm, awsbatch) with identical h5ad hashes, and only the slurm leg is waivable. T-31 requires a human-executed AWS Batch run (≤ $100) plus account, budget alarms and IAM setup (T-03). On 2026-09-16 local and slurm (Discovery) both completed with identical hashes (`docs/03_cross_profile_hashes.md`). The human then decided not to use AWS at all.

## Options

1. Keep F7 as written and leave the project incomplete until an AWS run happens.
2. Waive the awsbatch leg: keep `conf/awsbatch.config` and `docs/aws_setup.md` as configuration-only deliverables, mark T-31/T-03-AWS waived, and count F7 as satisfied by two schedulers (local executor, SLURM) and two container engines (Docker, singularity-ce).
3. Replace AWS with another paid cloud (same cost objection).

## Choice

Option 2. The cross-scheduler reproducibility claim F7 was meant to test is already evidenced by local vs SLURM; AWS would add a third scheduler at a monetary cost the human does not want to pay.

## Consequences

- PLAN.md §1 F7 reads "local·slurm·awsbatch, awsbatch waivable by 010"; T-03 AWS items and T-31 are marked waived in `docs/progress.md` under Waivers, with this record as the reason.
- README run-statistics and `docs/03` awsbatch rows say "waived (010)"; the awsbatch profile stays in the repo untested on AWS and is labelled as such.
- T-42 résumé wording can never claim AWS Batch execution; "configured for AWS Batch" is not claimed either (PLAN T-42 rule: no evidence, no claim).
- CLAUDE.md rule 9 (never run anything that costs money) becomes moot for this project.
