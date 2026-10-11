"""synthetic.py — fake typing for demos and tests. Never real patient data."""

from __future__ import annotations

import random

POOLS = {
    "A": ["A*01:01", "A*02:01", "A*02:03", "A*03:01", "A*11:01", "A*24:02", "A*29:02", "A*68:01"],
    "B": ["B*07:02", "B*08:01", "B*15:01", "B*15:03", "B*35:01", "B*44:02", "B*51:01", "B*57:01"],
    "C": ["C*03:03", "C*03:04", "C*04:01", "C*06:02", "C*07:01", "C*07:02"],
    "DRB1": ["DRB1*01:01", "DRB1*03:01", "DRB1*04:01", "DRB1*07:01", "DRB1*11:01", "DRB1*15:01"],
    "DQB1": ["DQB1*02:01", "DQB1*03:01", "DQB1*03:02", "DQB1*05:01", "DQB1*06:02"],
}


def demo_text(n: int = 5, seed: int = 7) -> str:
    """Tab-separated rows, like a block copied from Excel."""
    rng = random.Random(seed)
    lines = []
    for i in range(1, n + 1):
        cells = [f"SYN{i:04d}"]
        for pool in POOLS.values():
            cells += [rng.choice(pool), rng.choice(pool)]
        lines.append("\t".join(cells))
    return "\n".join(lines)
