"""Shared fixtures: small WMDA-format files and a fake GitHub — no network needed."""

from __future__ import annotations

import hashlib

import pytest

from hla_sero import imgt, wmda

REL_DNA_SER = """\
A*;01:01:01:01;1;;;;1
A*;01:01:01:02N;0;;;;
A*;01:01:38L;;0/1;;;1
A*;02:01:01:01;0201;;;;0201
A*;02:01:01:02L;;0/0201;;;0201
A*;02:01:02;0201;;;;0201
A*;02:03:01:01;0203;;;;0203
A*;02:55:01;;;2;28;69
A*;24:02:01:01;2402;;;;2402
B*;15:01:01:01;1501;;;;1501
B*;15:01:01:02N;0;;;;
B*;15:02:01:01;1502;;;;1502
B*;15:03:01:01;1503;;;;1503
B*;15:16:01:01;1516;;;;1516
B*;44:02:01:01;4402;;;;4402
C*;03:03:01:01;9;;;;9
C*;03:04:01:01;0304;;;;0304
C*;17:01:01:01;?;;;;
DRB1*;03:01:01:01;17;;;;17
DRB1*;15:01:01:01;1501;;;;1501
DRB4*;01:01:01:01;53;;;;53
DQB1*;03:01:01:01;7;;;;7
DPB1*;04:01:01:01;0401;;;;0401
MICA*;008:01:01;;;;;
"""

REL_SER_SER = """\
A;2;;0201/0203
A;9;23/24;
A;24;;2402
B;12;44/45;
B;15;62/63/75/76/77;
B;44;;4402
B;62;;1501
B;63;;1516
B;70;71/72;
B;72;;1503
B;75;;1502
Cw;3;9/10;
Cw;10;;0304
DR;2;15/16;
DR;3;17/18;
DR;15;;1501
DQ;3;7/8/9;
"""

HLA_NOM_G = """\
A*;01:01:01:01/01:01:01:02N/01:01:38L;01:01:01G
A*;02:01:01:01/02:01:01:02L/02:01:02;02:01:01G
"""

HLA_NOM_P = """\
B*;15:01:01:01/15:01:01:02N;15:01P
"""


def wmda_files(version: str = "9.99.0", date: str = "2099-01-01") -> dict[str, bytes]:
    body = {"rel_dna_ser.txt": REL_DNA_SER, "rel_ser_ser.txt": REL_SER_SER,
            "hla_nom_g.txt": HLA_NOM_G, "hla_nom_p.txt": HLA_NOM_P}
    out = {}
    for name, text in body.items():
        header = (f"# file: {name}\n# date: {date}\n# version: IPD-IMGT/HLA {version}\n"
                  f"# origin: test\n# repository: test\n# author: test\n")
        out[name] = (header + text).encode()
    out["md5checksum.txt"] = "".join(
        f"MD5 ({n}) = {hashlib.md5(b).hexdigest()}\n" for n, b in out.items()).encode()
    return out


@pytest.fixture
def db(tmp_path):
    for name, blob in wmda_files().items():
        (tmp_path / name).write_bytes(blob)
    return wmda.load(tmp_path)


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Isolated data/config folder for update tests."""
    monkeypatch.setenv("HLA_SERO_HOME", str(tmp_path / "home"))
    return tmp_path / "home"


@pytest.fixture
def github(monkeypatch):
    """Fake GitHub: refs maps branch name -> files. Mutate it inside a test."""
    refs = {"Latest": wmda_files("9.99.0"), "9990": wmda_files("9.99.0")}
    state = {"online": True, "calls": 0}

    def fake_fetch(url, timeout=30):
        state["calls"] += 1
        if not state["online"]:
            raise imgt.UpdateError("cannot reach GitHub (offline)")
        ref, name = url.split("/IMGTHLA/")[1].split("/wmda/")
        try:
            return refs[ref][name]
        except KeyError:
            raise imgt.UpdateError(f"{url} -> HTTP 404") from None

    monkeypatch.setattr(imgt, "_fetch", fake_fetch)
    return refs, state
