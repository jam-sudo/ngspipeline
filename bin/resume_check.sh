#!/usr/bin/env bash
# T-21: prove that `-resume` re-executes only the interrupted process and everything downstream of it.
# 1) run the test profile, kill Nextflow as soon as the quantification process (KALLISTOBUSTOOLS_COUNT) is submitted,
# 2) re-run with -resume, 3) tabulate CACHED vs executed tasks from the two execution traces.
# Usage: bin/resume_check.sh <outdir> [profile]   (default profile: test,docker)
set -euo pipefail
out="${1:?outdir}"; profile="${2:-test,docker}"
here="$(cd "$(dirname "$0")/.." && pwd)"
work="$out/work"; mkdir -p "$out"
kill_on='KALLISTOBUSTOOLS_COUNT'

echo "== run 1: kill when $kill_on is submitted"
( cd "$here" && nextflow run . -profile "$profile" --outdir "$out/run1" -work-dir "$work" > "$out/run1.log" 2>&1 ) &
nf=$!
for _ in $(seq 1 600); do
  if grep -q "Submitted process > .*${kill_on}" "$out/run1.log" 2>/dev/null; then
    echo "   $kill_on submitted -> sending SIGTERM to nextflow (pid $nf)"; kill -TERM "$nf"; break
  fi
  if ! kill -0 "$nf" 2>/dev/null; then echo "   run 1 ended before $kill_on was submitted"; break; fi
  sleep 1
done
wait "$nf" || true
run1_trace=$(ls -t "$out"/run1/pipeline_info/execution_trace_*.txt 2>/dev/null | head -1 || true)

echo "== run 2: -resume"
( cd "$here" && nextflow run . -profile "$profile" --outdir "$out/run2" -work-dir "$work" -resume > "$out/run2.log" 2>&1 )
run2_trace=$(ls -t "$out"/run2/pipeline_info/execution_trace_*.txt | head -1)

echo "== run 1 tasks (status)"; [ -n "$run1_trace" ] && cut -f4,5 "$run1_trace" | column -t || echo "   (no trace written for run 1)"
echo "== run 2 tasks (status): CACHED = reused from run 1, COMPLETED = executed in run 2"
cut -f4,5 "$run2_trace" | column -t
echo "== summary"; printf "CACHED: %s\nCOMPLETED: %s\n" "$(awk -F'\t' 'NR>1 && $5=="CACHED"' "$run2_trace" | wc -l | xargs)" "$(awk -F'\t' 'NR>1 && $5=="COMPLETED"' "$run2_trace" | wc -l | xargs)"
grep -E "Pipeline completed" "$out/run2.log" | tail -1
