"""Cross-check: the lab's existing serology vs the computed equivalent."""

import pytest

from hla_sero.crosscheck import extract_entries, normalise
from hla_sero.engine import convert_text


def _checks(db, text):
    return [(r["input"], r["expected"], r["check"]) for r in convert_text(db, text)]


def test_pairs_layout(db):
    assert _checks(db, "S1\tA*02:01\tA2\tB*15:03\tB72\tB*15:01\tB75") == [
        ("A*02:01", "A2", "match"), ("B*15:03", "B72", "match"), ("B*15:01", "B75", "mismatch")]


def test_alleles_then_antigens_layout(db):
    assert _checks(db, "S2  A*01:01  B*15:16  C*03:04   A1  B63  C10") == [
        ("A*01:01", "A1", "match"), ("B*15:16", "B63", "match"), ("C*03:04", "Cw10", "match")]


def test_broad_entered_is_broad_match(db):
    rows = convert_text(db, "S A*24:02 A9  DRB1*03:01 DR3")
    assert [r["check"] for r in rows] == ["broad-match", "broad-match"]
    assert "computed split is A24" in rows[0]["check_note"]


def test_legacy_three_digit_associated_name_matches(db):
    r = convert_text(db, "S A*02:03 A203")[0]
    assert r["check"] == "match" and r["associated"] == "A0203"


def test_null(db):
    assert _checks(db, "S A*01:01:01:02N null") == [("A*01:01:01:02N", "null", "match")]
    assert _checks(db, "S A*01:01:01:02N A1")[0][2] == "mismatch"


def test_match_on_uncertain_result_asks_for_review(db):
    r = convert_text(db, "S B*15:01/15:03 B62")[0]
    assert r["check"] == "match" and "review" in r["check_note"]


def test_sample_ids_that_look_like_antigens_are_not_expected_values(db):
    rows = convert_text(db, "B12\tA*02:01\tA*24:02")
    assert [r["sample"] for r in rows] == ["B12", "B12"]
    assert [r["expected"] for r in rows] == ["", ""]


def test_missing_expected_leaves_check_empty(db):
    rows = convert_text(db, "S A*02:01 A2 DQB1*03:01")
    assert [r["check"] for r in rows] == ["match", ""]


@pytest.mark.parametrize("raw, norm", [("c10", "Cw10"), ("Cw10", "Cw10"), ("dr17", "DR17"),
                                       ("NULL", "null"), ("dq7", "DQ7"), ("a2", "A2")])
def test_normalise(raw, norm):
    assert normalise(raw) == norm


def test_extract_entries_keeps_plain_typing_unchanged():
    assert extract_entries("S1\tA*02:01\tA*24:02") == [(1, "S1", "A*02:01", ""), (1, "S1", "A*24:02", "")]


def test_comment_column_is_never_read_as_serology(db):
    # Sample, Allele, Current serology (empty), comment that mentions antigens
    rows = convert_text(db, "VAL010,B*15:01,,B15 family -> B62\nVAL011\tB*15:03\tB72\tsplit of B70")
    assert [(r["expected"], r["check"]) for r in rows] == [("", ""), ("B72", "match")]


def test_excel_rows_with_expected_column(db):
    text = "SYN0001\tA*02:01\tA2\nSYN0001\tB*15:03\tB15\nSYN0002\tB*44:02\tB45\n"
    assert [r["check"] for r in convert_text(db, text)] == ["match", "mismatch", "mismatch"]


def test_alleles_then_antigens_in_excel_columns(db):
    rows = convert_text(db, "S2\tA*01:01\tB*15:16\tC*03:04\tA1\tB63\tC10")
    assert [r["expected"] for r in rows] == ["A1", "B63", "Cw10"]


def test_comma_separated_prose_without_expected(db):
    rows = convert_text(db, "Patient 2: A*01:01:01G, A*02:03, B*15:03")
    assert [r["expected"] for r in rows] == ["", "", ""] and rows[0]["sample"] == "Patient 2"
