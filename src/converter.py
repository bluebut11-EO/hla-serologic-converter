"""
converter.py — molecular HLA (IMGT/HLA allele) -> UNOS serologic equivalent.

This is the LOGIC LAYER: the piece that sits between molecular typing and the
serologic antigen vocabulary a virtual crossmatch (vXM) is expressed in.

Design notes for the learner:
- Standard library only. No pandas here on purpose, so every transformation is
  visible. (You'll add pandas at the CLI/data-wrangling layer in week 2.)
- The mapping is done at the ALLELE FAMILY level (first field, e.g. A*24:xx -> A24)
  as a deliberate simplification. The real IMGT/HLA `rel_dna_ser.txt` assigns
  serology per allele because some alleles in a family carry a different, null,
  or "expert-assigned" serologic equivalent. Replacing the reference table with
  that file (and switching the key from family to full allele) is a future TODO.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

# Expression suffixes that may trail an allele name (N=null, Q=questionable, etc.)
EXPRESSION_SUFFIXES = set("NLSCAQ")

# Accepts: "A*24:02", "HLA-A*24:02:01:01", "DRB1*15:01", with optional suffix.
_ALLELE_RE = re.compile(
    r"^(?:HLA-)?"
    r"(?P<locus>[A-Z]+[0-9]*)\*"
    r"(?P<first>\d+)"
    r"(?::(?P<second>\d+))?"   # second field, e.g. the "01" in B*15:01
    r"(?::\d+)*"
    r"(?P<suffix>[A-Z])?$"
)

# Allele-level exceptions live next to the family table and are checked first.
OVERRIDES_FILENAME = "allele_overrides.csv"


@dataclass
class ConversionResult:
    raw: str
    locus: str | None = None
    family: str | None = None
    serologic_split: str | None = None
    serologic_broad: str | None = None
    status: str = "unparseable"  # unparseable | unmapped | mapped
    level: str | None = None     # which table answered: "allele" | "family"

    def __str__(self) -> str:
        if self.status == "mapped":
            return (f"{self.raw} -> {self.serologic_split} "
                    f"(broad {self.serologic_broad}, {self.level}-level)")
        return f"{self.raw} -> [{self.status}]"


def normalize_allele(raw: str) -> tuple[str, str] | None:
    """Return (locus, first_field_family) or None if it can't be parsed.

    >>> normalize_allele("HLA-A*24:02:01")
    ('A', '24')
    >>> normalize_allele("DRB1*15:01")
    ('DRB1', '15')
    >>> normalize_allele("nonsense")
    """
    parsed = parse_allele(raw)
    return None if parsed is None else (parsed[0], parsed[1])


def parse_allele(raw: str) -> tuple[str, str, str | None] | None:
    """Return (locus, family, two_field) e.g. ('B', '15', '15:01').

    two_field is None when only one field was given (e.g. "A*02").
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    m = _ALLELE_RE.match(s)
    if not m:
        return None
    suffix = m.group("suffix")
    if suffix and suffix not in EXPRESSION_SUFFIXES:
        return None  # a stray trailing letter that isn't a known suffix
    locus = m.group("locus")
    # zero-pad single-digit families so "A*2" and "A*02" both key as "02"
    family = m.group("first").zfill(2)
    second = m.group("second")
    two_field = f"{family}:{second}" if second else None
    return locus, family, two_field


def _read_table(path: Path, key_column: str) -> dict[tuple[str, str], dict[str, str]]:
    table: dict[tuple[str, str], dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader((ln for ln in fh if not ln.startswith("#"))):
            table[(row["locus"], row[key_column])] = {
                "serologic_split": row["serologic_split"],
                "serologic_broad": row["serologic_broad"],
            }
    return table


def load_reference(path: str | Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load the family table, plus allele_overrides.csv from the same folder.

    Keys look like ("A", "24") for families and ("B", "15:01") for alleles,
    so both kinds can live in one dict without colliding.
    """
    path = Path(path)
    table = _read_table(path, "family")
    overrides = path.parent / OVERRIDES_FILENAME
    if overrides.exists():
        table.update(_read_table(overrides, "allele"))
    return table


def to_serologic(raw: str, reference: dict[tuple[str, str], dict[str, str]]) -> ConversionResult:
    """Convert one molecular allele string to its serologic equivalent.

    Lookup order: allele-level (two-field) first, then family-level.
    A family with no family-level row (like B*15) stays "unmapped" when the
    specific allele isn't listed — an honest "unknown" beats a wrong answer.
    """
    parsed = parse_allele(raw)
    if parsed is None:
        return ConversionResult(raw=raw, status="unparseable")
    locus, family, two_field = parsed

    for key, level in (((locus, two_field), "allele"), ((locus, family), "family")):
        entry = reference.get(key) if key[1] else None
        if entry is not None:
            return ConversionResult(
                raw=raw,
                locus=locus,
                family=family,
                serologic_split=entry["serologic_split"],
                serologic_broad=entry["serologic_broad"],
                status="mapped",
                level=level,
            )
    return ConversionResult(raw=raw, locus=locus, family=family, status="unmapped")


if __name__ == "__main__":
    ref = load_reference(Path(__file__).resolve().parents[1] / "data/reference/serologic_equivalents.csv")
    for example in ["A*01:01", "HLA-A*24:02:01", "DRB1*15:01", "B*44:02", "A*99:01", "junk"]:
        print(to_serologic(example, ref))
