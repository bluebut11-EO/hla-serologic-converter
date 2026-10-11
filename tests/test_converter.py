"""
test_converter.py — runs under pytest OR as a plain script:

    python -m tests.test_converter     # no pytest needed
    pytest                             # if installed
"""

from pathlib import Path

from src.converter import load_reference, normalize_allele, to_serologic

REF = load_reference(Path(__file__).resolve().parents[1] / "data/reference/serologic_equivalents.csv")


def test_normalize_strips_prefix_and_fields():
    assert normalize_allele("HLA-A*24:02:01:01") == ("A", "24")
    assert normalize_allele("A*02:01") == ("A", "02")
    assert normalize_allele("DRB1*15:01") == ("DRB1", "15")


def test_normalize_pads_single_digit():
    assert normalize_allele("A*2") == ("A", "02")


def test_normalize_rejects_junk():
    assert normalize_allele("nonsense") is None
    assert normalize_allele("") is None


def test_basic_mapping():
    r = to_serologic("A*01:01", REF)
    assert r.status == "mapped" and r.serologic_split == "A1" and r.serologic_broad == "A1"


def test_split_and_broad():
    r = to_serologic("A*24:02", REF)
    assert r.serologic_split == "A24" and r.serologic_broad == "A9"
    r2 = to_serologic("DRB1*15:01", REF)
    assert r2.serologic_split == "DR15" and r2.serologic_broad == "DR2"


def test_unmapped_allele_is_flagged():
    r = to_serologic("A*99:01", REF)
    assert r.status == "unmapped" and r.locus == "A" and r.family == "99"


def test_unparseable():
    assert to_serologic("garbage", REF).status == "unparseable"

def test_dr9_dr10():
    assert to_serologic("DRB1*09:01", REF).serologic_split == "DR9"
    assert to_serologic("DRB1*10:01", REF).serologic_split == "DR10"

def test_b15_splits_at_allele_level():
    # Same B*15 family, different serology -> family-level lookup can't tell them apart
    assert to_serologic("B*15:01", REF).serologic_split == "B62"
    assert to_serologic("B*15:02", REF).serologic_split == "B75"
    assert to_serologic("B*15:16", REF).serologic_split == "B63"
    r = to_serologic("B*15:03", REF)
    assert r.serologic_split == "B72" and r.serologic_broad == "B70"


def test_b15_unknown_allele_is_not_guessed():
    # A B*15 allele not in the override table must stay unmapped, never guessed
    assert to_serologic("B*15:99", REF).status == "unmapped"

def _run_all():
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS  {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed.")


if __name__ == "__main__":
    _run_all()
