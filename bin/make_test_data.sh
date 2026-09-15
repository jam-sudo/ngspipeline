#!/usr/bin/env bash
# Regenerate assets/test_data from the original FASTQs (T-10). Deterministic: sha256 of outputs is stable.
# Usage: bin/make_test_data.sh <fastq_dir> <ensembl_primary_assembly.fa.gz> <ensembl.gtf.gz> <library_pairs.csv> [outdir]
#   fastq_dir must contain <run>_1.fastq.gz / <run>_2.fastq.gz for every run in assets/test_data/runs_lane4.tsv
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
fastq_dir="${1:?fastq_dir}"; fasta="${2:?fasta}"; gtf="${3:?gtf}"; pairs="${4:?library_pairs.csv}"; outdir="${5:-$here/assets/test_data}"
python3 "$here/bin/make_test_data.py" \
  --fastq-dir "$fastq_dir" \
  --runs "$here/assets/test_data/runs_lane4.tsv" \
  --selection "$here/assets/test_data/selected_barcodes.tsv" \
  --genes "$here/assets/test_data/selected_genes.tsv" \
  --fasta "$fasta" --gtf "$gtf" --library-pairs "$pairs" \
  --outdir "$outdir" \
  --gex-frac 0.05 --bg-frac 0.02 --guide-frac 0.1 --flank 500 --extra-vectors 6
