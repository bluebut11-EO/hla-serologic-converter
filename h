[1mdiff --git a/src/converter.py b/src/converter.py[m
[1mindex 05dbe84..1bb49cb 100644[m
[1m--- a/src/converter.py[m
[1m+++ b/src/converter.py[m
[36m@@ -29,10 +29,14 @@[m [m_ALLELE_RE = re.compile([m
     r"^(?:HLA-)?"[m
     r"(?P<locus>[A-Z]+[0-9]*)\*"[m
     r"(?P<first>\d+)"[m
[32m+[m[32m    r"(?::(?P<second>\d+))?"   # second field, e.g. the "01" in B*15:01[m
     r"(?::\d+)*"[m
     r"(?P<suffix>[A-Z])?$"[m
 )[m
 [m
[32m+[m[32m# Allele-level exceptions live next to the family table and are checked first.[m
[32m+[m[32mOVERRIDES_FILENAME = "allele_overrides.csv"[m
[32m+[m
 [m
 @dataclass[m
 class ConversionResult:[m
[36m@@ -42,10 +46,12 @@[m [mclass ConversionResult:[m
     serologic_split: str | None = None[m
     serologic_broad: str | None = None[m
     status: str = "unparseable"  # unparseable | unmapped | mapped[m
[32m+[m[32m    level: str | None = None     # which table answered: "allele" | "family"[m
 [m
     def __str__(self) -> str:[m
         if self.status == "mapped":[m
[31m-            return f"{self.raw} -> {self.serologic_split} (broad {self.serologic_broad})"[m
[32m+[m[32m            return (f"{self.raw} -> {self.serologic_split} "[m
[32m+[m[32m                    f"(broad {self.serologic_broad}, {self.level}-level)")[m
         return f"{self.raw} -> [{self.status}]"[m
 [m
 [m
[36m@@ -58,6 +64,15 @@[m [mdef normalize_allele(raw: str) -> tuple[str, str] | None:[m
     ('DRB1', '15')[m
     >>> normalize_allele("nonsense")[m
     """[m
[32m+[m[32m    parsed = parse_allele(raw)[m
[32m+[m[32m    return None if parsed is None else (parsed[0], parsed[1])[m
[32m+[m
[32m+[m
[32m+[m[32mdef parse_allele(raw: str) -> tuple[str, str, str | None] | None:[m
[32m+[m[32m    """Return (locus, family, two_field) e.g. ('B', '15', '15:01').[m
[32m+[m
[32m+[m[32m    two_field is None when only one field was given (e.g. "A*02").[m
[32m+[m[32m    """[m
     if raw is None:[m
         return None[m
     s = raw.strip()[m
[36m@@ -72,39 +87,61 @@[m [mdef normalize_allele(raw: str) -> tuple[str, str] | None:[m
     locus = m.group("locus")[m
     # zero-pad single-digit families so "A*2" and "A*02" both key as "02"[m
     family = m.group("first").zfill(2)[m
[31m-    return locus, family[m
[32m+[m[32m    second = m.group("second")[m
[32m+[m[32m    two_field = f"{family}:{second}" if second else None[m
[32m+[m[32m    return locus, family, two_field[m
 [m
 [m
[31m-def load_reference(path: str | Path) -> dict[tuple[str, str], dict[str, str]]:[m
[31m-    """Load the serologic equivalence table into {(locus, family): {...}}."""[m
[32m+[m[32mdef _read_table(path: Path, key_column: str) -> dict[tuple[str, str], dict[str, str]]:[m
     table: dict[tuple[str, str], dict[str, str]] = {}[m
     with open(path, newline="", encoding="utf-8") as fh:[m
         for row in csv.DictReader((ln for ln in fh if not ln.startswith("#"))):[m
[31m-            key = (row["locus"], row["family"])[m
[31m-            table[key] = {[m
[32m+[m[32m            table[(row["locus"], row[key_column])] = {[m
                 "serologic_split": row["serologic_split"],[m
                 "serologic_broad": row["serologic_broad"],[m
             }[m
     return table[m
 [m
 [m
[32m+[m[32mdef load_reference(path: str | Path) -> dict[tuple[str, str], dict[str, str]]:[m
[32m+[m[32m    """Load the family table, plus allele_overrides.csv from the same folder.[m
[32m+[m
[32m+[m[32m    Keys look like ("A", "24") for families and ("B", "15:01") for alleles,[m
[32m+[m[32m    so both kinds can live in one dict without colliding.[m
[32m+[m[32m    """[m
[32m+[m[32m    path = Path(path)[m
[32m+[m[32m    table = _read_table(path, "family")[m
[32m+[m[32m    overrides = path.parent / OVERRIDES_FILENAME[m
[32m+[m[32m    if overrides.exists():[m
[32m+[m[32m        table.update(_read_table(overrides, "allele"))[m
[32m+[m[32m    return table[m
[32m+[m
[32m+[m
 def to_serologic(raw: str, reference: dict[tuple[str, str], dict[str, str]]) -> ConversionResult:[m
[31m-    """Convert one molecular allele string to its serologic equivalent."""[m
[31m-    parsed = normalize_allele(raw)[m
[32m+[m[32m    """Convert one molecular allele string to its serologic equivalent.[m
[32m+[m
[32m+[m[32m    Lookup order: allele-level (two-field) first, then family-level.[m
[32m+[m[32m    A family with no family-level row (like B*15) stays "unmapped" when the[m
[32m+[m[32m    specific allele isn't listed — an honest "unknown" beats a wrong answer.[m
[32m+[m[32m    """[m
[32m+[m[32m    parsed = parse_allele(raw)[m
     if parsed is None:[m
         return ConversionResult(raw=raw, status="unparseable")[m
[31m-    locus, family = parsed[m
[31m-    entry = reference.get((locus, family))[m
[31m-    if entry is None:[m
[31m-        return ConversionResult(raw=raw, locus=locus, family=family, status="unmapped")[m
[31m-    return ConversionResult([m
[31m-        raw=raw,[m
[31m-        locus=locus,[m
[31m-        family=family,[m
[31m-        serologic_split=entry["serologic_split"],[m
[31m-        serologic_broad=entry["serologic_broad"],[m
[31m-        status="mapped",[m
[31m-    )[m
[32m+[m[32m    locus, family, two_field = parsed[m
[32m+[m
[32m+[m[32m    for key, level in (((locus, two_field), "allele"), ((locus, family), "family")):[m
[32m+[m[32m        entry = reference.get(key) if key[1] else None[m
[32m+[m[32m        if entry is not None:[m
[32m+[m[32m            return ConversionResult([m
[32m+[m[32m                raw=raw,[m
[32m+[m[32m                locus=locus,[m
[32m+[m[32m                family=family,[m
[32m+[m[32m                serologic_split=entry["serologic_split"],[m
[32m+[m[32m                serologic_broad=entry["serologic_broad"],[m
[32m+[m[32m                status="mapped",[m
[32m+[m[32m                level=level,[m
[32m+[m[32m            )[m
[32m+[m[32m    return ConversionResult(raw=raw, locus=locus, family=family, status="unmapped")[m
 [m
 [m
 if __name__ == "__main__":[m
