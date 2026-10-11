"""Release-to-release comparison."""

from hla_sero import wmda
from hla_sero.diff import release_diff, render_markdown
from conftest import REL_DNA_SER, wmda_files


def _load(tmp_path, name, version, rel_dna_ser=None):
    files = wmda_files(version)
    if rel_dna_ser is not None:
        header = files["rel_dna_ser.txt"].decode().split("A*;", 1)[0]
        files["rel_dna_ser.txt"] = (header + rel_dna_ser).encode()
    d = tmp_path / name
    d.mkdir()
    for n, b in files.items():
        (d / n).write_bytes(b)
    return wmda.load(d)


def test_identical_releases_have_no_changes(tmp_path):
    a, b = _load(tmp_path, "a", "9.99.0"), _load(tmp_path, "b", "9.100.0")
    d = release_diff(a, b)
    assert d.changed == [] and d.new_groups == {} and d.removed == []


def test_detects_reclassification_new_and_removed(tmp_path):
    newer = (REL_DNA_SER
             .replace("A*;24:02:01:01;2402;;;;2402", "A*;24:02:01:01;;;24;;2402")   # unambiguous -> assumed
             .replace("B*;15:16:01:01;1516;;;;1516\n", "")                          # removed
             + "B*;15:99:01;1501;;;;1501\n")                                        # new, characterised
    d = release_diff(_load(tmp_path, "a", "9.99.0"), _load(tmp_path, "b", "9.100.0", newer))
    assert [(c.allele, c.old, c.new) for c in d.changed] == [("A*24:02", "A24 / A9 (mapped)", "A24 / A9 (assumed)")]
    assert d.removed == ["B*15:16"]
    assert d.new_groups == {"B*15:99": "B62 / B15 (mapped)"}
    md = render_markdown(d)
    assert "9.99.0 → 9.100.0" in md and "`A*24:02`" in md and "`B*15:99` B62 / B15" in md
