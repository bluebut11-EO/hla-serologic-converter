"""
generate_synthetic.py — make fake HLA typing data. NO real patient data, ever.

Produces a wide CSV: one row per synthetic sample, two alleles per locus,
mirroring how typing results are often stored. A few intentionally "unmapped"
alleles are sprinkled in so the converter's unmapped path gets exercised.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

# Allele pools per locus. Most map via the reference table; a couple (marked)
# deliberately do NOT, to test the "unmapped" branch.
POOLS = {
    "A": ["A*01:01", "A*02:01", "A*03:01", "A*11:01", "A*23:01", "A*24:02",
          "A*29:02", "A*32:01", "A*68:01", "A*99:01"],  # A*99 = unmapped on purpose
    "B": ["B*07:02", "B*08:01", "B*13:02", "B*27:05", "B*35:01", "B*44:02",
          "B*51:01", "B*57:01", "B*58:01"],
    "C": ["C*01:02", "C*03:04", "C*04:01", "C*05:01", "C*06:02", "C*07:01"],
    "DRB1": ["DRB1*01:01", "DRB1*03:01", "DRB1*04:01", "DRB1*07:01", "DRB1*11:01",
             "DRB1*13:01", "DRB1*15:01", "DRB1*16:01"],
}
LOCI = ["A", "B", "C", "DRB1"]


def make_samples(n: int, seed: int = 7) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        row = {"sample_id": f"SYN{i:04d}"}
        for locus in LOCI:
            a1, a2 = rng.choice(POOLS[locus]), rng.choice(POOLS[locus])
            row[f"{locus}_1"], row[f"{locus}_2"] = a1, a2
        rows.append(row)
    return rows


def write_csv(rows: list[dict[str, str]], path: str | Path) -> None:
    fieldnames = ["sample_id"] + [f"{l}_{i}" for l in LOCI for i in (1, 2)]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HLA typing data (no PHI).")
    parser.add_argument("-n", "--num", type=int, default=20, help="number of samples")
    parser.add_argument("-o", "--out", default="data/synthetic/sample_typing.csv")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_csv(make_samples(args.num, args.seed), out)
    print(f"Wrote {args.num} synthetic samples -> {out}")


if __name__ == "__main__":
    main()
