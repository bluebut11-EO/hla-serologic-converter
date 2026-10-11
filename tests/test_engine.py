"""Conversion rules, checked against small WMDA-format fixtures."""

import pytest

from hla_sero.engine import convert, convert_text, extract_tokens


@pytest.mark.parametrize("typing, equivalent, broad, associated, status", [
    ("A*01:01", "A1", "A1", "", "mapped"),
    ("A*02:01", "A2", "A2", "A0201", "mapped"),
    ("A*24:02", "A24", "A9", "A2402", "mapped"),
    ("B*15:01", "B62", "B15", "B1501", "mapped"),
    ("B*15:02", "B75", "B15", "B1502", "mapped"),
    ("B*15:03", "B72", "B70", "B1503", "mapped"),     # split of B70, not B15
    ("B*15:16", "B63", "B15", "B1516", "mapped"),
    ("B*44:02", "B44", "B12", "B4402", "mapped"),
    ("C*03:03", "Cw9", "Cw3", "", "mapped"),
    ("C*03:04", "Cw10", "Cw3", "Cw0304", "mapped"),
    ("DRB1*03:01", "DR17", "DR3", "", "mapped"),
    ("DRB1*15:01", "DR15", "DR2", "DR1501", "mapped"),  # same code as B*15:01, different locus
    ("DRB4*01:01", "DR53", "DR53", "", "mapped"),
    ("DQB1*03:01", "DQ7", "DQ3", "", "mapped"),
    ("HLA-A*24:02:01:01", "A24", "A9", "A2402", "mapped"),
])
def test_known_equivalents(db, typing, equivalent, broad, associated, status):
    r = convert(db, typing)
    assert (r.equivalent, r.broad, r.associated, r.status) == (equivalent, broad, associated, status)


def test_two_field_excludes_null_members(db):
    r = convert(db, "B*15:01")
    assert r.status == "mapped" and "N/Q excluded" in r.resolved_as and r.note == ""


def test_null_allele(db):
    r = convert(db, "A*01:01:01:02N")
    assert r.status == "null" and r.equivalent == "null"


def test_low_expression_allele_warns(db):
    r = convert(db, "A*02:01:01:02L")
    assert r.equivalent == "A2" and "may be null" in r.note


def test_assumed_is_flagged_never_silent(db):
    r = convert(db, "A*02:55:01")
    assert r.status == "assumed" and r.equivalent == "A2" and r.hats == "A69"


def test_ambiguity_string_lists_all_candidates(db):
    for typing in ("B*15:01/15:03", "B*15:01/B*15:03"):
        r = convert(db, typing)
        assert r.status == "ambiguous" and r.equivalent == "B62/B72" and r.broad == "B15/B70"


def test_family_level_is_ambiguous_not_guessed(db):
    r = convert(db, "B*15")
    assert r.status == "ambiguous" and set(r.equivalent.split("/")) == {"B62", "B63", "B72", "B75"}


def test_g_and_p_groups(db):
    g = convert(db, "A*01:01:01G")
    assert g.status == "mapped" and g.equivalent == "A1" and g.resolved_as.startswith("G group")
    p = convert(db, "B*15:01P")
    assert p.equivalent == "B62" and p.resolved_as.startswith("P group")


def test_xx_code(db):
    r = convert(db, "A*02:XX")
    assert r.equivalent == "A2" and r.associated == "A0201/A0203"


@pytest.mark.parametrize("typing, status", [
    ("C*17:01", "no-equivalent"),     # WMDA '?'
    ("MICA*008:01", "no-equivalent"), # locus without serology
    ("A*02:AB", "unsupported"),       # NMDP MAC
    ("A*99:99", "not-found"),
    ("A*01:01:01G9", "unparseable"),
])
def test_everything_else_is_reported_not_guessed(db, typing, status):
    assert convert(db, typing).status == status


def test_lab_override_wins(db):
    ov = {"A*02:03": {"equivalent": "A203", "broad": "A2", "note": "UNOS listing"}}
    r = convert(db, "A*02:03", ov)
    assert r.equivalent == "A203" and r.basis == "lab override"


def test_extract_tokens_from_messy_paste():
    text = ("SYN0001\tA*02:01\tA*24:02\n"
            "Patient 2: A*01:01:01G, B*15:01/15:03\n"
            "HLA-A: A*02:01, A*24:02\n"
            "no alleles on this line\n")
    got = extract_tokens(text)
    assert got[0] == (1, "SYN0001", "A*02:01")
    assert (2, "Patient 2", "B*15:01/15:03") in got
    assert got[-1] == (3, "", "A*24:02")        # a bare locus label is not a sample name
    assert len(got) == 6


def test_convert_text_rows(db):
    rows = convert_text(db, "S1\tA*02:01\tB*15:03")
    assert [(r["sample"], r["equivalent"]) for r in rows] == [("S1", "A2"), ("S1", "B72")]


def test_unsuffixed_name_finds_suffixed_allele(db):
    r = convert(db, "A*01:01:01:02")       # the allele exists only as ...02N
    assert r.status == "null"


def test_four_digit_fields_are_read_whole(db):
    # A*02:1294 must never be read as A*02:129 (a different allele)
    toks = [t for _l, _s, t in extract_tokens("S1 A*02:1294 B*07:02 DPB1*1000:01")]
    assert toks == ["A*02:1294", "B*07:02", "DPB1*1000:01"]
    assert convert(db, "A*02:1294").resolved_as == "exact allele"
    assert convert(db, "DPB1*1000:01").status == "no-equivalent"


def test_malformed_name_is_shown_not_truncated(db):
    rows = convert_text(db, "S1 A*02:12945 A*02:01")
    assert [(r["input"], r["status"]) for r in rows] == [("A*02:12945", "unparseable"), ("A*02:01", "mapped")]


def test_glued_prefix_is_kept_whole_and_reported(db):
    # never silently drop the "X" and convert it as A*02:01
    rows = convert_text(db, "XA*02:01 A*24:02")
    assert [(r["input"], r["status"]) for r in rows] == [("XA*02:01", "not-found"), ("A*24:02", "mapped")]
