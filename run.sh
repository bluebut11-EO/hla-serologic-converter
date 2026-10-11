#!/usr/bin/env bash
# run.sh — reproduce the whole pipeline with one command:
#   synthetic data -> conversion -> summary
#
#   ./run.sh            # 20 synthetic samples
#   ./run.sh 100        # 100 synthetic samples
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "No .venv found. Run ./setup.sh first."
    exit 1
fi
PY=.venv/bin/python
N="${1:-20}"

$PY -m src.generate_synthetic -n "$N"
$PY -m src.cli

OUT=data/synthetic/sample_converted.csv
echo
echo "== Output preview (first 3 rows) =="
head -n 4 "$OUT" | cut -c1-160
echo
echo "== Unmapped cells (alleles missing from the reference table) =="
grep -o "unmapped" "$OUT" | wc -l
