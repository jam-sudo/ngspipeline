#!/usr/bin/env bash
# Per-lane concordance of the pipeline's assignment with the authors' gem_group cells (T-14c / docs/01 per-lane table).
# Usage: bin/compare_lanes.sh <results_dir> <authors_dir with gg<N>_cells.tsv> <out_dir> <min_umi> lane1 lane2 ...
# Each lane's sample is replogle_k562_essential_lane<N>; reads results_dir/guides/<sample>/assignment.tsv and counts/<sample>/counts_{un,}filtered barcodes.
set -euo pipefail
res="$1"; auth="$2"; out="$3"; min_umi="$4"; shift 4
mkdir -p "$out"
for lane in "$@"; do
  s="replogle_k562_essential_lane${lane}"
  cdir="$res/counts/$s"
  args=()
  [ -f "$cdir/counts_unfiltered/cells_x_genes.barcodes.txt" ] && args+=(--unfiltered-barcodes "$cdir/counts_unfiltered/cells_x_genes.barcodes.txt")
  [ -f "$cdir/counts_filtered/cells_x_genes.barcodes.txt" ] && args+=(--filtered-barcodes "$cdir/counts_filtered/cells_x_genes.barcodes.txt")
  python3 "$(dirname "$0")/compare_assignments.py" --assignment "$res/guides/$s/assignment.tsv" --authors "$auth/gg${lane}_cells.tsv" \
    --min-umi "$min_umi" --label "lane_${lane} vs gem_group ${lane}" --out "$out/lane${lane}.md" --discordant-out "$out/lane${lane}_discordant.tsv" "${args[@]}" > /dev/null
  echo "lane $lane: $(grep 'concordant (single, same vector)' "$out/lane${lane}.md" | sed 's/.*| //; s/ |$//')"
done
