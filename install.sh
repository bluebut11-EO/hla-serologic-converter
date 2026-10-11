#!/usr/bin/env bash
# install.sh — install the hla-sero app for this user (Linux Mint / Ubuntu).
#   ./install.sh        install or upgrade from this folder
# Afterwards: "HLA Serology Converter" in the menu, or `hla-sero gui` in a terminal.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v pipx >/dev/null 2>&1; then
    echo "== pipx is needed to install Python apps. Installing it (asks for your password)..."
    sudo apt update && sudo apt install -y pipx
fi
pipx ensurepath >/dev/null 2>&1 || true
export PATH="$HOME/.local/bin:$PATH"

echo "== Installing hla-sero"
pipx install --force . >/dev/null
hla-sero --version

echo "== Downloading the latest IPD-IMGT/HLA release"
hla-sero update

echo "== Adding the menu entry"
hla-sero install-launcher

echo
echo "Done. Open 'HLA Serology Converter' from the Mint menu,"
echo "or run:  hla-sero gui     (open a new terminal first if the command is not found)"
