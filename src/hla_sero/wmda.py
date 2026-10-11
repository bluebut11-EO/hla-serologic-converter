"""
wmda.py — load the WMDA files published by IPD-IMGT/HLA into memory.

Files (all from https://github.com/ANHIG/IMGTHLA, folder wmda/):

  rel_dna_ser.txt   allele -> serological equivalent, 7 ';'-separated fields
                    1 locus   2 allele   3 unambiguous   4 possible
                    5 assumed 6 expert (registry search determinants)
                    7 HATS algorithm assignment
  rel_ser_ser.txt   antigen hierarchy: locus;broad;splits;associated
                    e.g.  B;15;62/63/75/76/77;      B;62;;1501/1520/...
  hla_nom_g.txt     G groups:  locus;member/member/...;GROUPNAME
  hla_nom_p.txt     P groups:  same layout

Under the 2026 HLA nomenclature many alleles map to four-digit
*associated antigens* (B*15:01 -> "1501", which belongs to B62, a split of
broad B15). rel_ser_ser.txt is what lets us walk that chain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

FILES = ("rel_dna_ser.txt", "rel_ser_ser.txt", "hla_nom_g.txt", "hla_nom_p.txt")

# Molecular locus -> prefix used for serological antigens in rel_ser_ser.txt
SEROLOGY_PREFIX = {
    "A": "A", "B": "B", "C": "Cw",
    "DRB1": "DR", "DRB3": "DR", "DRB4": "DR", "DRB5": "DR",
    "DQB1": "DQ",
    # No classical serology hierarchy for these; labelled for readability only
    "DQA1": "DQA", "DPB1": "DP", "DPA1": "DPA",
}

EXPRESSION_SUFFIXES = "NLSCAQ"
_VERSION_RE = re.compile(r"#\s*version:\s*IPD-IMGT/HLA\s+([\d.]+)")
_DATE_RE = re.compile(r"#\s*date:\s*(\S+)")


@dataclass(frozen=True)
class AlleleRecord:
    locus: str            # "B"
    name: str             # "15:01:01:01" (may carry a suffix, e.g. "01:01:01:02N")
    unambiguous: str      # field 3: "1501", "0" (null), "?" (no equivalent) or ""
    possible: str         # field 4: "0/0201"
    assumed: str          # field 5
    expert: str           # field 6
    hats: str             # field 7

    @property
    def suffix(self) -> str:
        return self.name[-1] if self.name and self.name[-1] in EXPRESSION_SUFFIXES else ""

    @property
    def fields(self) -> list[str]:
        base = self.name[:-1] if self.suffix else self.name
        return base.split(":")


@dataclass
class Database:
    version: str
    date: str
    alleles: dict[tuple[str, str], AlleleRecord] = field(default_factory=dict)
    # (locus, "15:01") -> records whose name starts with that prefix; also 1- and 3-field
    by_prefix: dict[tuple[str, str], list[AlleleRecord]] = field(default_factory=dict)
    assoc_parent: dict[tuple[str, str], str] = field(default_factory=dict)   # (B,"1501") -> "62"
    split_broad: dict[tuple[str, str], str] = field(default_factory=dict)    # (B,"62") -> "15"
    g_groups: dict[tuple[str, str], list[str]] = field(default_factory=dict) # (A,"01:01:01G") -> names
    p_groups: dict[tuple[str, str], list[str]] = field(default_factory=dict)

    def summary(self) -> str:
        return f"IPD-IMGT/HLA {self.version} ({self.date}), {len(self.alleles):,} alleles"


def _data_lines(path: Path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line and not line.startswith("#"):
                yield line


def read_header(path: Path) -> tuple[str, str]:
    """Return (version, date) from a WMDA file's six-line header."""
    version = date = ""
    with open(path, encoding="utf-8") as fh:
        for _ in range(10):
            line = fh.readline()
            if not line.startswith("#"):
                break
            if m := _VERSION_RE.match(line):
                version = m.group(1)
            if m := _DATE_RE.match(line):
                date = m.group(1)
    return version, date


def load(folder: str | Path) -> Database:
    folder = Path(folder)
    missing = [f for f in FILES if not (folder / f).exists()]
    if missing:
        raise FileNotFoundError(f"missing WMDA files in {folder}: {', '.join(missing)}")

    version, date = read_header(folder / "rel_dna_ser.txt")
    db = Database(version=version, date=date)

    for line in _data_lines(folder / "rel_dna_ser.txt"):
        parts = (line.split(";") + [""] * 7)[:7]
        locus = parts[0].rstrip("*")
        rec = AlleleRecord(locus, *parts[1:7])
        db.alleles[(locus, rec.name)] = rec
        f = rec.fields
        for n in range(1, len(f)):            # index by 1-, 2- and 3-field prefixes
            db.by_prefix.setdefault((locus, ":".join(f[:n])), []).append(rec)

    for line in _data_lines(folder / "rel_ser_ser.txt"):
        prefix, antigen, splits, assoc = (line.split(";") + [""] * 4)[:4]
        for s in filter(None, splits.split("/")):
            db.split_broad[(prefix, s)] = antigen
        for a in filter(None, assoc.split("/")):
            db.assoc_parent[(prefix, a)] = antigen

    for fname, target in (("hla_nom_g.txt", db.g_groups), ("hla_nom_p.txt", db.p_groups)):
        for line in _data_lines(folder / fname):
            locus, members, group = (line.split(";") + [""] * 3)[:3]
            if group:
                target[(locus.rstrip("*"), group)] = members.split("/")

    return db
