#!/usr/bin/env bash
# setup.sh — developer setup: editable install in .venv + run the tests.
# (To just USE the app, run ./install.sh instead.)
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
    python3 -m venv .venv || { echo "Run: sudo apt install python3-venv"; exit 1; }
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -e ".[dev]"
.venv/bin/python -m pytest -q
echo
echo "Dev setup complete. Try:  .venv/bin/hla-sero demo | .venv/bin/hla-sero convert"
echo "Live check against the real IMGT/HLA release:  HLA_SERO_LIVE=1 .venv/bin/python -m pytest tests/test_live.py"
