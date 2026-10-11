"""
cli.py — convert a synthetic typing CSV into serologic equivalents.

This is the layer where you DO use pandas (week-2 skill): read a table,
apply the converter cell by cell, write an output table. Run:

    python -m src.cli --in data/synthetic/sample_typing.csv \
                      --out data/synthetic/sample_converted.csv

Or convert a single allele:

    python -m src.cli --allele "A*24:02"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .converter import load_reference, to_serologic

REF_PATH = Path(__file__).resolve().parents[1] / "data/reference/serologic_equivalents.csv"


def convert_table(in_path: str, out_path: str) -> pd.DataFrame:
    ref = load_reference(REF_PATH)
    df = pd.read_csv(in_path, dtype=str)
    allele_cols = [c for c in df.columns if c != "sample_id"]

    out = df[["sample_id"]].copy()
    for col in allele_cols:
        results = df[col].map(lambda a: to_serologic(a, ref))
        out[f"{col}_split"] = results.map(lambda r: r.serologic_split)
        out[f"{col}_broad"] = results.map(lambda r: r.serologic_broad)
        out[f"{col}_status"] = results.map(lambda r: r.status)

    out.to_csv(out_path, index=False)
    n_unmapped = (out.filter(like="_status") == "unmapped").to_numpy().sum()
    print(f"Converted {len(out)} samples -> {out_path}  ({n_unmapped} unmapped cells flagged)")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Molecular HLA -> serologic equivalent converter.")
    parser.add_argument("--allele", help="convert a single allele and exit")
    parser.add_argument("--in", dest="in_path", default="data/synthetic/sample_typing.csv")
    parser.add_argument("--out", dest="out_path", default="data/synthetic/sample_converted.csv")
    args = parser.parse_args()

    if args.allele:
        print(to_serologic(args.allele, load_reference(REF_PATH)))
        return
    convert_table(args.in_path, args.out_path)


if __name__ == "__main__":
    main()
