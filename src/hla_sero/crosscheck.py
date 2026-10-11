"""
crosscheck.py — compare the lab's existing serology with the computed equivalent.

Paste the allele next to the serology you already have, in either layout:

  S1   A*02:01  A2   A*24:02  A24   B*15:03  B72          (pairs)
  S1   A*02:01  A*24:02  B*15:03   A2  A24  B72           (alleles, then antigens)
  S1   A*01:01:01:02N  null

Only text AFTER the first allele on a line is read as serology, so sample IDs
such as "B12" or "A100" at the start of a line are never mistaken for antigens.

Tab/comma-separated rows (Excel, CSV) are read by column: the expected value must
be the cell right after the allele. An empty cell means "no expected value", and
comment columns further right are never read as serology.

check values:
  match           expected = computed antigen (or its associated antigen)
  broad-match     expected is the broad of the computed split (e.g. A9 for A24)
  mismatch        anything else — review
  (empty)         no expected value was given for that allele
"""

from __future__ import annotations

import re

from .engine import TOKEN_RE, _LOCUS_LABEL_RE

# Serological antigen names a lab would write: A2, B62, Cw10, C10, DR17, DQ7, DR52, A203
SERO_RE = re.compile(r"(?<![\w*:])(?:Cw|DPw|DR|DQ|DP|A|B|C)\d{1,4}(?![\w*:])|(?<![\w*])null(?!\w)", re.I)
_SPLIT_PREFIX = re.compile(r"^([A-Za-z]+)(\d+)$")


def normalise(antigen: str) -> str:
    """'c10' -> 'Cw10', 'dr17' -> 'DR17', 'NULL' -> 'null'."""
    a = antigen.strip()
    if a.lower() == "null":
        return "null"
    m = _SPLIT_PREFIX.match(a)
    if not m:
        return a
    prefix, num = m.group(1).upper(), m.group(2)
    prefix = {"C": "Cw", "CW": "Cw", "DPW": "DPw"}.get(prefix, prefix)
    return prefix + num


def _numeric(label: str) -> tuple[str, int] | None:
    """'A0203' and 'A203' both -> ('A', 203): old 3-digit vs 2026 4-digit associated names."""
    m = _SPLIT_PREFIX.match(label)
    return (m.group(1), int(m.group(2))) if m else None


_DELIMS = re.compile(r"[\t,;|]")


def _is_sero(cell: str) -> bool:
    return bool(SERO_RE.fullmatch(cell.strip()))


def extract_entries(text: str) -> list[tuple[int, str, str, str]]:
    """Return (line_number, sample, allele_token, expected_serology_or_empty)."""
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        alleles = list(TOKEN_RE.finditer(line))
        if not alleles:
            continue
        lead = line[: alleles[0].start()].strip(" \t,;:|-=")
        sample = "" if _LOCUS_LABEL_RE.fullmatch(lead) else lead[:60]
        delimited = bool(_DELIMS.search(line))

        own, following = [], []          # serology right after each allele / run of serology after it
        for k, m in enumerate(alleles):
            end = alleles[k + 1].start() if k + 1 < len(alleles) else len(line)
            gap = line[m.end():end]
            if delimited:
                cells = [c.strip() for c in _DELIMS.split(gap)]
                rest_of_cell, next_cells = cells[0], cells[1:]
                tokens = rest_of_cell.split() if rest_of_cell else next_cells[:1]
                run = []
                for c in (rest_of_cell.split() + next_cells if rest_of_cell else next_cells):
                    if not _is_sero(c):
                        break
                    run.append(normalise(c))
            else:
                tokens = gap.split()
                run = []
                for t in tokens:
                    if not _is_sero(t):
                        break
                    run.append(normalise(t))
            first = tokens[0] if tokens else ""
            own.append(normalise(first) if first and _is_sero(first) else "")
            following.append(run)

        n = len(alleles)
        if n > 1 and not any(own[:-1]) and len(following[-1]) == n:
            expected = following[-1]          # alleles first, then antigens in the same order
        else:
            expected = own
        out += [(i, sample, m.group(0), e) for m, e in zip(alleles, expected)]
    return out


def compare(row: dict, expected: str) -> tuple[str, str]:
    """(check, note) for one converted row against the lab's expected serology."""
    if not expected:
        return "", ""
    status = row["status"]
    equivalents = [x for x in row["equivalent"].split("/") if x]
    associated = [x for x in row["associated"].split("/") if x]
    broads = [x for x in row["broad"].split("/") if x]
    review = f"computed result is '{status}' — review" if status in ("assumed", "ambiguous") else ""

    if expected == "null":
        return ("match", "") if status == "null" else ("mismatch", f"expected null, computed {row['equivalent'] or status}")
    if status == "null":
        return "mismatch", f"computed null (not expressed), expected {expected}"
    if expected.lower() in (e.lower() for e in equivalents):
        return "match", review
    want = _numeric(expected)
    if want and any(_numeric(a) == want for a in associated):
        return "match", "; ".join(filter(None, ["matches the associated antigen", review]))
    if expected.lower() in (b.lower() for b in broads) and expected.lower() not in (e.lower() for e in equivalents):
        return "broad-match", f"expected is the broad; computed split is {row['equivalent']}"
    if row.get("hats") and expected in row["hats"].split("/"):
        return "mismatch", f"matches only the HATS prediction ({row['hats']}); computed {row['equivalent'] or status}"
    return "mismatch", f"computed {row['equivalent'] or status}" + (f" (broad {row['broad']})" if row["broad"] else "")


def summary(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        if r.get("check"):
            counts[r["check"]] = counts.get(r["check"], 0) + 1
    return counts
