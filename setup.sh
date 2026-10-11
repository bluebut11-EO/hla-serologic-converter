#!/usr/bin/env bash
# setup.sh — one-time environment setup (Linux Mint / Ubuntu).
# Creates a private Python environment in .venv, installs dependencies,
# and runs the test suite. Safe to re-run.
#
#   ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/4  Python check =="
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found. Run:  sudo apt install python3"
    exit 1
fi
python3 --version

echo "== 2/4  Virtual environment (.venv) =="
if [ ! -d .venv ]; then
    if ! python3 -m venv .venv 2>/dev/null; then
        rm -rf .venv
        echo "venv module missing. Run:  sudo apt install python3-venv"
        echo "then re-run ./setup.sh"
        exit 1
    fi
    echo "created .venv"
else
    echo ".venv already exists"
fi

echo "== 3/4  Install dependencies =="
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
.venv/bin/python -c "import pandas, pytest; print('pandas', pandas.__version__, '| pytest', pytest.__version__)"

echo "== 4/4  Tests =="
.venv/bin/python -m pytest -q

echo
echo "Setup complete. Next:  ./run.sh"
