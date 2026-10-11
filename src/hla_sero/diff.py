"""
diff.py — what changed in the serological equivalents between two IMGT/HLA releases.

Compares every 2-field allele group (A*02:01, B*15:03 ...) of the loci that have
serology, converted with exactly the same rules the app uses. This is the list a
lab needs before moving to a new release:

  changed   equivalent, broad or status differs (e.g. assumed -> mapped)
  new       2-field groups that did not exist in the older release
  removed   2-field groups no longer present
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .engine import convert
from .wmda import SEROLOGY_PREFIX, Database


@dataclass
class Change:
    allele: str
    old: str          # "B62 / B15 (mapped)"
    new: str


@dataclass
class ReleaseDiff:
    old_version: str
    new_version: str
    groups_old: int = 0
    groups_new: int = 0
    changed: list[Change] = field(default_factory=list)
    new_groups: dict[str, str] = field(default_factory=dict)       # allele -> summary
    removed: list[str] = field(default_factory=list)

    @property
    def new_by_status(self) -> Counter:
        return Counter(s.rsplit("(", 1)[-1].rstrip(")") for s in self.new_groups.values())


def two_field_groups(db: Database) -> set[tuple[str, str]]:
    groups = set()
    for (locus, _name), rec in db.alleles.items():
        if locus in SEROLOGY_PREFIX:
            f = rec.fields
            if len(f) >= 2:
                groups.add((locus, ":".join(f[:2])))
    return groups


def _summary(db: Database, locus: str, group: str) -> str:
    r = convert(db, f"{locus}*{group}")
    shown = r.equivalent or "-"
    if r.broad and r.broad != r.equivalent:
        shown += f" / {r.broad}"
    return f"{shown} ({r.status})"


def release_diff(old: Database, new: Database) -> ReleaseDiff:
    g_old, g_new = two_field_groups(old), two_field_groups(new)
    d = ReleaseDiff(old.version, new.version, len(g_old), len(g_new))
    for locus, group in sorted(g_old & g_new):
        a, b = _summary(old, locus, group), _summary(new, locus, group)
        if a != b:
            d.changed.append(Change(f"{locus}*{group}", a, b))
    for locus, group in sorted(g_new - g_old):
        d.new_groups[f"{locus}*{group}"] = _summary(new, locus, group)
    d.removed = [f"{l}*{g}" for l, g in sorted(g_old - g_new)]
    return d


def render_markdown(d: ReleaseDiff, max_rows: int = 200) -> str:
    lines = [
        f"## Serology changes: IPD-IMGT/HLA {d.old_version} → {d.new_version}",
        "",
        f"2-field groups with serology loci: {d.groups_old:,} → {d.groups_new:,}",
        f"- **Changed equivalents/status: {len(d.changed)}**",
        f"- New 2-field groups: {len(d.new_groups)}"
        + (" (" + ", ".join(f"{n} {s}" for s, n in d.new_by_status.most_common()) + ")" if d.new_groups else ""),
        f"- Removed 2-field groups: {len(d.removed)}",
        "",
    ]
    if d.changed:
        lines += ["### Changed (re-check these before moving to the new release)", "",
                  f"| Allele | {d.old_version} | {d.new_version} |", "|---|---|---|"]
        lines += [f"| `{c.allele}` | {c.old} | {c.new} |" for c in d.changed[:max_rows]]
        if len(d.changed) > max_rows:
            lines.append(f"| … | {len(d.changed) - max_rows} more | |")
        lines.append("")
    else:
        lines += ["No existing 2-field group changed its serological equivalent or status.", ""]
    mapped_new = {a: s for a, s in d.new_groups.items() if s.endswith("(mapped)")}
    if mapped_new:
        lines += ["### New groups with characterised serology", "",
                  ", ".join(f"`{a}` {s.split(' (')[0]}" for a, s in list(mapped_new.items())[:max_rows]), ""]
    if d.removed:
        lines += ["### Removed", "", ", ".join(f"`{a}`" for a in d.removed[:max_rows]), ""]
    return "\n".join(lines)


def render_text(d: ReleaseDiff, max_rows: int = 200) -> str:
    out = [f"IPD-IMGT/HLA {d.old_version} -> {d.new_version}",
           f"  changed: {len(d.changed)}   new 2-field groups: {len(d.new_groups)}   removed: {len(d.removed)}"]
    if d.changed:
        w = max(len(c.allele) for c in d.changed[:max_rows])
        out.append("")
        out += [f"  {c.allele:<{w}}  {c.old}  ->  {c.new}" for c in d.changed[:max_rows]]
    return "\n".join(out)
