# 004 — Repo / pipeline naming

Status: accepted (2026-09-15)
Task: T-00

## Context

Working directory is `~/NGSpipeline`. Plan drafts used `alive-upstream`. nf-core template needs a pipeline name (lowercase, no hyphens recommended for the Nextflow manifest name).

## Options

- `ngspipeline` (matches directory)
- `aliveupstream` / `alive-upstream` (states purpose)
- other

## Choice

`ngspipeline`. Decided by the human on 2026-09-15.

- Nextflow manifest name: `ngspipeline`
- GitHub remote: `github.com/jam-sudo/ngspipeline` (assumed from the name; confirm at T-00 `git remote -v`)
- Downstream consumer: ALIVE at https://github.com/jam-sudo/alive

## Consequences

Name must be consistent in: GitHub repo, `nextflow.config` manifest, README, PLAN.md, résumé line (T-42).
`alive-upstream` is no longer used anywhere; purpose is stated in the README description instead of the name.

Branch layout follows the nf-core template (T-00): `master` = releases, `dev` = integration, `TEMPLATE` = pristine template for `nf-core pipelines sync`. Task branches `T-##` open PRs against `dev`; the template's `branch.yml` rejects PRs to `master` from anything but `dev`. Where PLAN.md says "main 브랜치 보호", read `dev` (and `master`).
