"""The weekly watch script's helpers."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "imgt_watch", Path(__file__).resolve().parents[1] / "packaging" / "imgt_watch.py")
imgt_watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imgt_watch)


def test_branch_to_version():
    assert imgt_watch.branch_to_version("3650") == "3.65.0"
    assert imgt_watch.branch_to_version("3170") == "3.17.0"
    assert imgt_watch.branch_to_version("3100") == "3.10.0"
    assert imgt_watch.branch_to_version("Latest") is None
    assert imgt_watch.branch_to_version("testing") is None
