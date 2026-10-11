"""Download, verification and update policy — against a fake GitHub."""

import pytest

from hla_sero import imgt
from conftest import wmda_files


def test_first_run_downloads_latest(home, github):
    db = imgt.load_database(log=lambda m: None)
    assert db.version == "9.99.0"
    assert imgt.installed_releases() == ["9.99.0"]
    assert imgt.load_state()["current"] == "9.99.0"


def test_checksum_mismatch_is_rejected(home, github):
    refs, _ = github
    refs["Latest"]["rel_dna_ser.txt"] += b"A*;99:99;99;;;;\n"     # tampered after md5 was computed
    with pytest.raises(imgt.UpdateError, match="checksum mismatch"):
        imgt.download_release("Latest", log=lambda m: None)
    assert imgt.installed_releases() == []


def test_auto_mode_switches_to_new_release_and_keeps_old(home, github):
    refs, _ = github
    imgt.load_database(log=lambda m: None)
    refs["Latest"] = wmda_files("9.100.0")                        # IMGT publishes a release
    db = imgt.check_and_update(force=True, log=lambda m: None)
    assert db == "9.100.0"
    assert imgt.installed_releases() == ["9.99.0", "9.100.0"]     # numeric, not text, ordering


def test_check_interval_limits_network_use(home, github):
    _, state = github
    imgt.load_database(log=lambda m: None)
    calls = state["calls"]
    imgt.load_database(log=lambda m: None)                        # within 7 days: no check
    assert state["calls"] == calls


def test_notify_mode_does_not_switch(home, github):
    refs, _ = github
    imgt.load_database(log=lambda m: None)
    imgt.save_config({**imgt.load_config(), "auto_update": "notify", "check_interval_days": 0})
    refs["Latest"] = wmda_files("9.100.0")
    messages = []
    assert imgt.check_and_update(log=messages.append) == "9.99.0"
    assert any("9.100.0 available" in m for m in messages)


def test_off_mode_never_calls_network(home, github):
    _, state = github
    imgt.load_database(log=lambda m: None)
    imgt.save_config({**imgt.load_config(), "auto_update": "off", "check_interval_days": 0})
    calls = state["calls"]
    imgt.load_database(log=lambda m: None)
    assert state["calls"] == calls


def test_offline_uses_cache(home, github):
    _, state = github
    imgt.load_database(log=lambda m: None)
    imgt.save_config({**imgt.load_config(), "check_interval_days": 0})
    state["online"] = False
    messages = []
    assert imgt.load_database(log=messages.append).version == "9.99.0"
    assert any("using cached" in m for m in messages)


def test_offline_first_run_explains(home, github):
    _, state = github
    state["online"] = False
    with pytest.raises(imgt.UpdateError, match="cannot reach GitHub"):
        imgt.load_database(log=lambda m: None)


def test_pinned_release_is_used_even_when_newer_exists(home, github):
    refs, _ = github
    refs["Latest"] = wmda_files("9.100.0")
    imgt.save_config({**imgt.load_config(), "pinned_release": "9.99.0"})
    assert imgt.load_database(log=lambda m: None).version == "9.99.0"


def test_release_to_ref():
    assert imgt.release_to_ref("3.65.0") == "3650"
    assert imgt.release_to_ref(None) == "Latest"
    with pytest.raises(imgt.UpdateError):
        imgt.release_to_ref("latest-ish")


def test_unpin_returns_to_newest(home, github):
    refs, _ = github
    refs["Latest"] = wmda_files("9.100.0")
    imgt.load_database(log=lambda m: None)                        # installs 9.100.0
    imgt.save_config({**imgt.load_config(), "pinned_release": "9.99.0"})
    assert imgt.load_database(log=lambda m: None).version == "9.99.0"
    imgt.save_config({**imgt.load_config(), "pinned_release": None})
    assert imgt.load_database(log=lambda m: None).version == "9.100.0"
