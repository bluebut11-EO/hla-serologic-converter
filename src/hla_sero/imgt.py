"""
imgt.py — fetch, verify, cache and update the IPD-IMGT/HLA WMDA files.

Source: https://github.com/ANHIG/IMGTHLA
  * branch "Latest"  -> the newest release
  * branch "3650"    -> release 3.65.0 (one branch per release, for pinning)

Every release is stored in its own folder and never overwritten:

  ~/.local/share/hla-sero/releases/3.65.0/rel_dna_ser.txt ...
  ~/.local/share/hla-sero/state.json      {"current": "3.65.0", "last_check": ...}
  ~/.config/hla-sero/config.json          {"auto_update": "auto", ...}

Set HLA_SERO_HOME to keep everything in one folder instead (used by tests).

Downloads are verified against the md5checksum.txt published alongside the
files, and all four files must report the same release version before a
release is accepted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import wmda

RAW_URL = "https://raw.githubusercontent.com/ANHIG/IMGTHLA/{ref}/wmda/{name}"
USER_AGENT = "hla-serologic-converter (+https://github.com/bluebut11-EO/hla-serologic-converter)"
DEFAULT_CONFIG = {"auto_update": "auto", "check_interval_days": 7, "pinned_release": None}
AUTO_UPDATE_MODES = ("auto", "notify", "off")


class UpdateError(RuntimeError):
    pass


# ---------------------------------------------------------------- locations

def _home() -> Path | None:
    h = os.environ.get("HLA_SERO_HOME")
    return Path(h) if h else None


def data_dir() -> Path:
    if h := _home():
        return h
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "hla-sero"


def config_dir() -> Path:
    if h := _home():
        return h
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "hla-sero"


def releases_dir() -> Path:
    return data_dir() / "releases"


def _read_json(path: Path, default: dict) -> dict:
    try:
        return {**default, **json.loads(path.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return dict(default)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_config() -> dict:
    return _read_json(config_dir() / "config.json", DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    _write_json(config_dir() / "config.json", cfg)


def load_state() -> dict:
    return _read_json(data_dir() / "state.json", {"current": None, "last_check": None})


def save_state(state: dict) -> None:
    _write_json(data_dir() / "state.json", state)


def installed_releases() -> list[str]:
    d = releases_dir()
    if not d.exists():
        return []
    vs = [p.name for p in d.iterdir() if p.is_dir() and all((p / f).exists() for f in wmda.FILES)]
    return sorted(vs, key=_version_key)


def _version_key(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v))


def release_to_ref(release: str | None) -> str:
    """'3.65.0' -> '3650' (the IMGTHLA branch name); None -> 'Latest'."""
    if not release or release.lower() == "latest":
        return "Latest"
    digits = "".join(re.findall(r"\d", release))
    if not re.fullmatch(r"\d+\.\d+\.\d+", release) or not digits:
        raise UpdateError(f"release must look like 3.65.0, got {release!r}")
    return digits


# ---------------------------------------------------------------- network

def _fetch(url: str, timeout: float = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise UpdateError(f"{url} -> HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise UpdateError(f"cannot reach GitHub ({e})") from e


def remote_version(ref: str = "Latest") -> str:
    """Cheap check: read the version header of the small rel_ser_ser.txt."""
    text = _fetch(RAW_URL.format(ref=ref, name="rel_ser_ser.txt"), timeout=15).decode("utf-8", "replace")
    m = re.search(r"#\s*version:\s*IPD-IMGT/HLA\s+([\d.]+)", text)
    if not m:
        raise UpdateError("could not read the release version from GitHub")
    return m.group(1)


def download_release(ref: str = "Latest", log=print) -> str:
    """Download + verify one release into releases/<version>/. Returns the version."""
    log(f"Downloading IPD-IMGT/HLA WMDA files ({ref}) from GitHub...")
    checksums = {}
    md5_text = _fetch(RAW_URL.format(ref=ref, name="md5checksum.txt")).decode("utf-8", "replace")
    for m in re.finditer(r"MD5 \(([^)]+)\) = ([0-9a-f]{32})", md5_text):
        checksums[m.group(1)] = m.group(2)

    with tempfile.TemporaryDirectory(prefix="hla-sero-") as tmp:
        tmp = Path(tmp)
        versions = set()
        for name in wmda.FILES:
            blob = _fetch(RAW_URL.format(ref=ref, name=name), timeout=120)
            expected = checksums.get(name)
            actual = hashlib.md5(blob).hexdigest()
            if expected and actual != expected:
                raise UpdateError(f"{name}: checksum mismatch (expected {expected}, got {actual})")
            (tmp / name).write_bytes(blob)
            versions.add(wmda.read_header(tmp / name)[0])
            log(f"  {name:16} {len(blob)/1e6:5.1f} MB  {'md5 ok' if expected else 'no checksum listed'}")
        if len(versions) != 1 or "" in versions:
            raise UpdateError(f"files disagree on release version: {sorted(versions)}")
        version = versions.pop()
        wmda.load(tmp)                                  # must parse before we accept it

        dest = releases_dir() / version
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tmp, dest)
    log(f"Installed IPD-IMGT/HLA {version}")
    return version


# ---------------------------------------------------------------- policy

def check_and_update(force: bool = False, release: str | None = None, log=print) -> str | None:
    """Apply the update policy. Returns the release that should be used (or None).

    * pinned release (config or `release` argument) -> make sure it is installed, use it
    * auto   -> check GitHub at most every N days; install and switch to newer releases
    * notify -> check, but only tell the user
    * off    -> never touch the network unless forced or nothing is installed
    Network problems never block conversion when a cached release exists.
    """
    cfg, state = load_config(), load_state()
    installed = installed_releases()
    pinned = release or cfg.get("pinned_release")

    if pinned and pinned.lower() != "latest":
        if pinned not in installed:
            download_release(release_to_ref(pinned), log=log)
        state["current"] = pinned
        save_state(state)
        return pinned

    # Not pinned = follow the newest release we have (and look for newer ones below)
    current = installed[-1] if installed else None
    mode = cfg.get("auto_update", "auto")
    if current and not force:
        if mode == "off":
            return current
        last = state.get("last_check")
        interval = timedelta(days=float(cfg.get("check_interval_days", 7)))
        if last and datetime.now(timezone.utc) - datetime.fromisoformat(last) < interval:
            return current

    try:
        latest = remote_version("Latest")
    except UpdateError as e:
        if current:
            log(f"(update check skipped: {e}; using cached {current})")
            return current
        raise
    state["last_check"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if current and _version_key(latest) <= _version_key(current):
        save_state({**state, "current": current})
        if force:
            log(f"Already up to date: IPD-IMGT/HLA {current}")
        return current

    if current and mode == "notify" and not force:
        log(f"New IPD-IMGT/HLA release {latest} available (using {current}). Run: hla-sero update")
        save_state({**state, "current": current})
        return current

    version = latest if latest in installed else download_release("Latest", log=log)
    if current and version != current:
        log(f"Switched from IPD-IMGT/HLA {current} to {version}. Earlier releases are kept "
            f"(pin one with: hla-sero config --pin {current}).")
    state["current"] = version
    save_state(state)
    return version


def load_database(release: str | None = None, update: bool = True, log=print) -> wmda.Database:
    version = check_and_update(release=release, log=log) if update else load_state().get("current")
    if not version:
        installed = installed_releases()
        version = installed[-1] if installed else None
    if not version:
        raise UpdateError("no IPD-IMGT/HLA release installed yet. Run: hla-sero update")
    return wmda.load(releases_dir() / version)
