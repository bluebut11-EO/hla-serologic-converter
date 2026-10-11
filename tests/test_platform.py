"""Windows-specific behaviour, checked from any OS."""

from pathlib import Path

from hla_sero import cli, gui, imgt


def test_windows_folders(monkeypatch, tmp_path):
    monkeypatch.delenv("HLA_SERO_HOME", raising=False)
    monkeypatch.setattr(imgt, "_is_windows", lambda: True)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert imgt.data_dir() == Path(tmp_path / "Local" / "hla-sero")
    assert imgt.config_dir() == Path(tmp_path / "Roaming" / "hla-sero")


def test_double_clicked_exe_opens_gui(monkeypatch):
    called = {}
    monkeypatch.setattr(cli.sys, "frozen", True, raising=False)
    monkeypatch.setattr(cli, "cmd_gui", lambda args: called.setdefault("gui", True) and 0)
    cli.main([])
    assert called == {"gui": True}


def test_page_is_packaged():
    assert b"HLA Serology Converter" in gui._page()


def test_gui_settings_pin_and_mode(home, github):
    app = gui.App(release=None)
    app.configure({"auto_update": "notify", "pin": True})
    cfg = imgt.load_config()
    assert cfg["auto_update"] == "notify" and cfg["pinned_release"] == "9.99.0"
    app.configure({"pin": False})
    assert imgt.load_config()["pinned_release"] is None
