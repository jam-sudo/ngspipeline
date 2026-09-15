#!/usr/bin/env bash
# Build a prebuilt kallisto|bustools reference for --reference_index (docs/decisions/002).
# Uses the kallisto binary bundled in the nf-core kallistobustools module container, so the
# index version matches what KALLISTOBUSTOOLS_COUNT expects (kb-python 0.28.2).
# Usage: bin/build_reference_index.sh <cdna.fa.gz> <ncrna.fa.gz> <outdir> [threads]
set -euo pipefail
cdna="${1:?cdna.fa.gz}"; ncrna="${2:?ncrna.fa.gz}"; out="${3:?outdir}"; threads="${4:-6}"
img="quay.io/biocontainers/kb-python:0.28.2--pyhdfd78af_2"
kallisto="/usr/local/lib/python3.8/site-packages/kb_python/bins/linux/kallisto/kallisto"
mkdir -p "$out"; out="$(cd "$out" && pwd)"
cat "$cdna" "$ncrna" > "$out/transcripts.fa.gz"
# t2g: transcript_id <TAB> gene_id <TAB> gene_symbol, from Ensembl FASTA headers (">ENST... gene:ENSG... gene_symbol:XYZ")
gzip -dc "$out/transcripts.fa.gz" | awk '/^>/{tid=substr($1,2); g=""; gn=""; for(i=2;i<=NF;i++){ if($i ~ /^gene:/) g=substr($i,6); if($i ~ /^gene_symbol:/) gn=substr($i,13)} print tid"\t"g"\t"gn}' > "$out/t2g.txt"
docker run --rm --platform linux/amd64 -v "$out:/out" -w /out "$img" sh -c "$kallisto version && $kallisto index -t $threads -i index.idx transcripts.fa.gz"
ls -la "$out"
