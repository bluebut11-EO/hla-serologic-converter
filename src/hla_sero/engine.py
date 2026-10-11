"""
engine.py — turn molecular HLA typing into serological equivalents.

Accepted input (anything else is reported, never guessed):
  full allele      A*02:01:01:01, B*15:01:01:01, A*01:01:01:02N
  1-3 fields       A*02:01, B*15, DRB1*03:01:01
  G / P groups     A*01:01:01G, B*15:01P
  XX codes         A*02:XX
  ambiguity        B*15:01/15:03   or   B*15:01/B*15:03
  NMDP MAC codes   A*02:AB  -> "unsupported" (needs the NMDP MAC service)

Rules that matter clinically:
  * Serologically characterised assignments (fields 3-4 of rel_dna_ser) are
    the only ones reported as status "mapped".
  * An allele with no characterised serology falls back to the WMDA
    "assumed" value and is reported with status "assumed" — never silently.
  * When a typing without an expression suffix (e.g. A*01:01) covers null (N)
    or questionable (Q) alleles, those are excluded and the exclusion is noted.
  * If the alleles covered by one input disagree, the result is "ambiguous"
    and every candidate antigen is listed.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass

from .wmda import SEROLOGY_PREFIX, AlleleRecord, Database

# A field is digits (01, 101) or a letter code (XX, or an NMDP MAC like AB).
# Kept apart from the trailing one-letter suffix so "01:01:01G" parses as
# fields 01:01:01 + suffix G rather than a field "01G".
_FIELD = r"(?:\d{1,3}|[A-Z]{2,5})"
_ALLELE = rf"\d{{1,3}}(?::{_FIELD})*[A-Z]?"
_LOCUS = r"[A-Z]{1,4}\d?"

# Allele-like tokens inside arbitrary pasted text (with optional /alternatives)
TOKEN_RE = re.compile(rf"(?:HLA-)?{_LOCUS}\*{_ALLELE}(?:/(?:{_LOCUS}\*)?{_ALLELE})*")
_NAME_RE = re.compile(
    rf"^(?:HLA-)?(?P<locus>{_LOCUS})\*(?P<body>\d{{1,3}}(?::{_FIELD})*)(?P<suffix>[A-Z])?$"
)
# A bare locus heading like "HLA-A:" or "DRB1" is not a sample name ("S1" is)
_LOCUS_LABEL_RE = re.compile(r"(?:HLA-)?(?:A|B|C|DRB[1-9]|DQ[AB][12]|DP[AB][12]|MIC[AB])", re.I)

STATUS_ORDER = ["mapped", "assumed", "ambiguous", "null", "no-equivalent",
                "not-found", "unsupported", "unparseable"]


@dataclass
class Result:
    input: str
    locus: str = ""
    resolved_as: str = ""        # what the input expanded to, in words
    equivalent: str = ""         # antigen, e.g. B62  (or "B62/B72" when ambiguous)
    associated: str = ""         # associated antigen, e.g. B1501
    broad: str = ""              # broad, e.g. B15
    status: str = "unparseable"
    basis: str = ""              # unambiguous / possible / assumed (+ allele counts)
    hats: str = ""               # HATS algorithm assignment, shown for reference
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- serology walk

def _label(prefix: str, code: str) -> str:
    return f"{prefix}{code}" if code else ""


def resolve_code(db: Database, locus: str, code: str) -> tuple[str, str, str]:
    """Serology code from rel_dna_ser -> (antigen, associated, broad) labels.

    "1501" for locus B  ->  ("B62", "B1501", "B15")
    "9"    for locus C  ->  ("Cw9", "", "Cw3")
    """
    prefix = SEROLOGY_PREFIX.get(locus, locus)
    associated = ""
    antigen = code
    if (prefix, code) in db.assoc_parent:
        associated, antigen = code, db.assoc_parent[(prefix, code)]
    broad = db.split_broad.get((prefix, antigen), antigen)
    return _label(prefix, antigen), _label(prefix, associated), _label(prefix, broad)


def _allele_call(rec: AlleleRecord) -> tuple[str, list[str]]:
    """(basis, codes) for one allele, in order of evidence strength."""
    if rec.unambiguous:
        return "unambiguous", [rec.unambiguous]
    if rec.possible:
        return "possible", rec.possible.split("/")
    if rec.assumed:
        return "assumed", rec.assumed.split("/")
    return "none", []


# ---------------------------------------------------------------- input -> alleles

def _expand(db: Database, locus: str, body: str, suffix: str) -> tuple[list[AlleleRecord], str, str]:
    """Return (records, resolved_as description, error_status)."""
    fields = body.split(":")
    last = fields[-1]

    if suffix == "G" or suffix == "P":
        groups = db.g_groups if suffix == "G" else db.p_groups
        names = groups.get((locus, body + suffix))
        if names is None:
            return [], "", "not-found"
        recs = [db.alleles[(locus, n)] for n in names if (locus, n) in db.alleles]
        return recs, f"{suffix} group ({len(recs)} alleles)", ""

    if last == "XX":
        recs = db.by_prefix.get((locus, ":".join(fields[:-1])), [])
        return recs, f"XX code ({len(recs)} alleles)", "" if recs else "not-found"

    if any(re.search(r"[A-Z]", f) for f in fields):
        return [], "", "unsupported"         # NMDP MAC code such as 02:AB

    full = body + suffix
    if (locus, full) in db.alleles:
        return [db.alleles[(locus, full)]], "exact allele", ""

    recs = db.by_prefix.get((locus, body), [])
    if suffix:
        recs = [r for r in recs if r.suffix == suffix]
    if not recs:
        return [], "", "not-found"
    level = {1: "allele family", 2: "2-field", 3: "3-field"}.get(len(fields), "prefix")
    return recs, f"{level} ({len(recs)} alleles)", ""


def _split_alternatives(token: str) -> list[str]:
    """'B*15:01/15:03' -> ['B*15:01', 'B*15:03']"""
    parts = token.split("/")
    head = parts[0]
    locus_part = head.split("*")[0] + "*" if "*" in head else ""
    return [head] + [p if "*" in p else locus_part + p for p in parts[1:]]


# ---------------------------------------------------------------- main entry

def convert(db: Database, token: str, overrides: dict[str, dict] | None = None) -> Result:
    token = token.strip()
    res = Result(input=token)

    if overrides and token in overrides:
        o = overrides[token]
        res.locus = token.split("*")[0].removeprefix("HLA-")
        res.equivalent, res.associated, res.broad = o["equivalent"], o.get("associated", ""), o.get("broad", "")
        res.status, res.basis, res.resolved_as = "mapped", "lab override", "lab override table"
        res.note = o.get("note", "")
        return res

    records: list[AlleleRecord] = []
    described: list[str] = []
    for alt in _split_alternatives(token):
        m = _NAME_RE.match(alt)
        if not m:
            return res                                 # unparseable
        locus, body, suffix = m.group("locus"), m.group("body"), m.group("suffix") or ""
        if suffix and suffix not in "GP" + "NLSCAQ":
            return res
        res.locus = locus
        recs, how, err = _expand(db, locus, body, suffix)
        if err:
            res.status = err
            res.note = {
                "not-found": f"not in IPD-IMGT/HLA {db.version} (check spelling, or it may be renamed/deleted)",
                "unsupported": "NMDP MAC codes need the NMDP MAC service; expand to alleles first",
            }[err]
            return res
        records += recs
        described.append(how)
    res.resolved_as = " + ".join(described)
    if res.locus not in SEROLOGY_PREFIX:
        res.status, res.note = "no-equivalent", f"{res.locus} has no serological antigens"
        return res

    # A group of alleles (2-field, G group, XX...) means "an expressed allele";
    # drop the null/questionable members unless they are all there is.
    excluded = 0
    if len(records) > 1:
        kept = [r for r in records if r.suffix not in ("N", "Q")]
        if kept:
            excluded = len(records) - len(kept)
            records = kept

    calls = [(r, *_allele_call(r)) for r in records]
    hats = sorted({resolve_code(db, res.locus, r.hats)[0] for r in records if r.hats and r.hats not in "0?"})
    res.hats = "/".join(hats)

    notes = []          # only things a reviewer should look at
    if excluded:
        res.resolved_as += f", {excluded} N/Q excluded"

    def summarise(subset):
        antigens: Counter[str] = Counter()
        assoc, broads = set(), set()
        for _rec, _basis, codes in subset:
            for code in codes:
                a, s, b = resolve_code(db, res.locus, code)
                antigens[a] += 1
                if s:
                    assoc.add(s)
                broads.add(b)
        return antigens, assoc, broads

    total = len(calls)
    for basis_name in ("unambiguous", "possible", "assumed"):
        subset = [c for c in calls if c[1] == basis_name]
        if not subset:
            continue
        # null ("0") and no-equivalent ("?") codes are handled separately
        real = [(r, b, [c for c in codes if c not in ("0", "?")]) for r, b, codes in subset]
        real = [c for c in real if c[2]]
        nulls = sum(1 for _r, _b, codes in subset if codes == ["0"])
        unknown = sum(1 for _r, _b, codes in subset if codes == ["?"])

        if not real:
            if nulls and not unknown:
                res.status, res.equivalent = "null", "null"
                res.basis = f"{basis_name} ({nulls}/{total} alleles)"
                res.note = "; ".join(notes + ["not expressed at the cell surface"])
                return res
            if unknown:
                res.status = "no-equivalent"
                res.basis = f"{basis_name} ({unknown}/{total} alleles)"
                res.note = "; ".join(notes + ["WMDA lists no serological equivalent ('?')"])
                return res
            continue

        antigens, assoc, broads = summarise(real)
        res.equivalent = "/".join(sorted(antigens))
        res.associated = "/".join(sorted(assoc))
        res.broad = "/".join(sorted(broads))
        res.basis = f"{basis_name} ({len(real)}/{total} alleles)"
        if len(antigens) > 1:
            res.status = "ambiguous"
            notes.append("covered alleles map to different antigens: " +
                         ", ".join(f"{a} ×{n}" for a, n in antigens.most_common()))
        elif basis_name == "assumed":
            res.status = "assumed"
            notes.append("no serologically characterised allele; WMDA 'assumed' value from the allele name")
        else:
            res.status = "mapped"
            if basis_name == "possible":
                notes.append("WMDA 'possible' serology")
                if any("0" in codes for _r, _b, codes in subset):
                    notes.append("may be null / low-expressed")
        res.note = "; ".join(notes)
        return res

    res.status = "no-equivalent"
    res.note = "; ".join(notes + ["no serology fields populated for these alleles"])
    return res


def extract_tokens(text: str) -> list[tuple[int, str, str]]:
    """Find allele names in pasted text.

    Returns (line_number, sample_label, token). The sample label is the first
    cell on the line that is not itself an allele (e.g. a sample ID from Excel).
    """
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        matches = list(TOKEN_RE.finditer(line))
        if not matches:
            continue
        # Text before the first allele: "SYN0001<TAB>", "Patient 1: ", "HLA-A: "
        lead = line[: matches[0].start()].strip(" \t,;:|-=")
        sample = "" if _LOCUS_LABEL_RE.fullmatch(lead) else lead[:60]
        out += [(i, sample, m.group(0)) for m in matches]
    return out


def convert_text(db: Database, text: str, overrides: dict | None = None) -> list[dict]:
    rows = []
    for line_no, sample, token in extract_tokens(text):
        r = convert(db, token, overrides).as_dict()
        rows.append({"line": line_no, "sample": sample, **r})
    return rows
