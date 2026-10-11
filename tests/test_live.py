"""Optional: check the real, current IMGT/HLA release from GitHub.

    HLA_SERO_LIVE=1 python -m pytest tests/test_live.py -v
"""

import os

import pytest

from hla_sero import engine, imgt

pytestmark = [pytest.mark.live,
              pytest.mark.skipif(not os.environ.get("HLA_SERO_LIVE"), reason="set HLA_SERO_LIVE=1")]


@pytest.fixture(scope="module")
def live_db(tmp_path_factory):
    os.environ["HLA_SERO_HOME"] = str(tmp_path_factory.mktemp("live"))
    try:
        yield imgt.load_database(log=print)
    finally:
        os.environ.pop("HLA_SERO_HOME", None)


@pytest.mark.parametrize("typing, equivalent, broad", [
    ("A*02:01", "A2", "A2"), ("A*24:02", "A24", "A9"),
    ("B*15:01", "B62", "B15"), ("B*15:03", "B72", "B70"), ("B*44:02", "B44", "B12"),
    ("C*03:04", "Cw10", "Cw3"), ("DRB1*03:01", "DR17", "DR3"), ("DRB1*15:01", "DR15", "DR2"),
    ("DQB1*03:01", "DQ7", "DQ3"), ("DQB1*06:02", "DQ6", "DQ1"),
])
def test_real_release(live_db, typing, equivalent, broad):
    r = engine.convert(live_db, typing)
    assert (r.equivalent, r.broad, r.status) == (equivalent, broad, "mapped")
