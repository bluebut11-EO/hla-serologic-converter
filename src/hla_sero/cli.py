"""
hla-sero — molecular HLA typing -> serological equivalents (IPD-IMGT/HLA WMDA data)

  hla-sero gui                     open the copy-paste window in your browser
  hla-sero convert                 paste typing in the terminal, Ctrl+D to finish
  hla-sero convert typing.txt      convert a file (any text/CSV/TSV containing alleles)
  hla-sero convert -o out.csv x.txt   write CSV instead of printing a table
  hla-sero update [--release 3.64.0]  get the latest (or a specific) IMGT/HLA release
  hla-sero status                  which release is in use, update settings
  hla-sero config --auto-update auto|notify|off   [--pin 3.65.0 | --unpin]
  hla-sero install-launcher        add "HLA Serology Converter" to the Mint menu
  hla-sero demo                    print synthetic typing to try things out
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

from . import __version__, imgt
from .engine import convert_text

COLUMNS = ["line", "sample", "input", "equivalent", "associated", "broad",
           "status", "basis", "hats", "resolved_as", "note"]


def load_overrides() -> dict[str, dict]:
    """Optional lab policy table: ~/.config/hla-sero/overrides.csv
    columns: allele,equivalent,associated,broad,note  (allele exactly as typed)"""
    path = imgt.config_dir() / "overrides.csv"
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        rows = csv.DictReader(ln for ln in fh if not ln.startswith("#"))
        return {r["allele"].strip(): r for r in rows if r.get("allele")}


def provenance(db) -> str:
    return f"IPD-IMGT/HLA {db.version} ({db.date}) via WMDA rel_dna_ser/rel_ser_ser"


def _print_table(rows: list[dict], db) -> None:
    cols = ["sample", "input", "equivalent", "broad", "associated", "status", "basis"]
    width = {c: max([len(c)] + [len(str(r[c])) for r in rows]) for c in cols}
    width = {c: min(w, 28) for c, w in width.items()}
    fmt = "  ".join(f"{{{c}:<{width[c]}.{width[c]}}}" for c in cols)
    print(f"# {provenance(db)}")
    print(fmt.format(**{c: c.upper() for c in cols}))
    for r in rows:
        print(fmt.format(**{c: str(r[c]) for c in cols}))
    notes = [(r["input"], r["note"]) for r in rows if r["note"]]
    if notes:
        print("\nNotes:")
        for token, note in notes:
            print(f"  {token}: {note}")


def write_rows(rows: list[dict], db, out, delimiter: str = ",") -> None:
    out.write(f"# {provenance(db)}\n")
    w = csv.DictWriter(out, fieldnames=COLUMNS, delimiter=delimiter, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)


def cmd_convert(args) -> int:
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    else:
        if sys.stdin.isatty():
            print("Paste typing (any format), then press Enter and Ctrl+D:", file=sys.stderr)
        text = sys.stdin.read()
    db = imgt.load_database(release=args.release, update=not args.offline, log=_err)
    rows = convert_text(db, text, load_overrides())
    if not rows:
        _err("No HLA allele names found (expected e.g. A*02:01, B*15:01:01G, DRB1*03:01).")
        return 1
    if args.output:
        delim = "\t" if args.output.endswith((".tsv", ".txt")) else ","
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            write_rows(rows, db, fh, delim)
        _err(f"Wrote {len(rows)} rows -> {args.output}  ({provenance(db)})")
    elif args.format in ("csv", "tsv"):
        write_rows(rows, db, sys.stdout, "\t" if args.format == "tsv" else ",")
    else:
        _print_table(rows, db)
    return 0


def cmd_update(args) -> int:
    if args.release:
        version = imgt.download_release(imgt.release_to_ref(args.release))
        print(f"Release {version} installed. Use it with: hla-sero config --pin {version}")
    else:
        imgt.check_and_update(force=True)
    return 0


def cmd_status(_args) -> int:
    cfg, state = imgt.load_config(), imgt.load_state()
    print(f"hla-sero {__version__}")
    print(f"In use        : {state.get('current') or '(none yet — run hla-sero update)'}")
    print(f"Installed     : {', '.join(imgt.installed_releases()) or '-'}")
    print(f"Auto-update   : {cfg['auto_update']} (check every {cfg['check_interval_days']} days)")
    print(f"Pinned release: {cfg.get('pinned_release') or '-'}")
    print(f"Last check    : {state.get('last_check') or '-'}")
    print(f"Data folder   : {imgt.data_dir()}")
    ov = imgt.config_dir() / "overrides.csv"
    print(f"Lab overrides : {ov if ov.exists() else '- (optional: ' + str(ov) + ')'}")
    return 0


def cmd_config(args) -> int:
    cfg = imgt.load_config()
    if args.auto_update:
        cfg["auto_update"] = args.auto_update
    if args.interval is not None:
        cfg["check_interval_days"] = args.interval
    if args.pin:
        imgt.release_to_ref(args.pin)            # validates the format
        cfg["pinned_release"] = args.pin
    if args.unpin:
        cfg["pinned_release"] = None
    imgt.save_config(cfg)
    if args.pin:
        imgt.check_and_update(release=args.pin)
    return cmd_status(args)


def cmd_gui(args) -> int:
    from .gui import serve
    return serve(port=args.port, open_browser=not args.no_browser, release=args.release)


def cmd_install_launcher(_args) -> int:
    exe = shutil.which("hla-sero") or f"{sys.executable} -m hla_sero"
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    desktop = apps / "hla-sero.desktop"
    desktop.write_text(
        "[Desktop Entry]\nType=Application\nName=HLA Serology Converter\n"
        "Comment=Molecular HLA typing to serological equivalents (IPD-IMGT/HLA)\n"
        f"Exec={exe} gui\nIcon=applications-science\nTerminal=false\n"
        "Categories=Science;MedicalSoftware;Education;\n", encoding="utf-8")
    desktop.chmod(0o755)
    print(f"Menu entry created: {desktop}\nFind it in the Mint menu as 'HLA Serology Converter'.")
    return 0


def cmd_demo(args) -> int:
    from .synthetic import demo_text
    print(demo_text(args.num))
    return 0


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hla-sero", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"hla-sero {__version__}")
    sub = p.add_subparsers(dest="cmd")

    c = sub.add_parser("convert", help="convert pasted text or a file")
    c.add_argument("file", nargs="?", help="text/CSV/TSV file; omit to paste")
    c.add_argument("-o", "--output", help="write CSV (.csv) or TSV (.tsv/.txt)")
    c.add_argument("--format", choices=["table", "csv", "tsv"], default="table")
    c.add_argument("--release", help="use a specific IMGT/HLA release, e.g. 3.64.0")
    c.add_argument("--offline", action="store_true", help="never check for updates")
    c.set_defaults(func=cmd_convert)

    u = sub.add_parser("update", help="download the latest (or a given) IMGT/HLA release")
    u.add_argument("--release", help="e.g. 3.64.0")
    u.set_defaults(func=cmd_update)

    sub.add_parser("status", help="show release and settings").set_defaults(func=cmd_status)

    cf = sub.add_parser("config", help="change update settings")
    cf.add_argument("--auto-update", choices=imgt.AUTO_UPDATE_MODES)
    cf.add_argument("--interval", type=float, help="days between update checks")
    cf.add_argument("--pin", help="always use this release, e.g. 3.65.0")
    cf.add_argument("--unpin", action="store_true", help="follow the latest release again")
    cf.set_defaults(func=cmd_config)

    g = sub.add_parser("gui", help="open the copy-paste window in your browser")
    g.add_argument("--port", type=int, default=0, help="default: a free port")
    g.add_argument("--no-browser", action="store_true")
    g.add_argument("--release")
    g.set_defaults(func=cmd_gui)

    sub.add_parser("install-launcher", help="add a menu entry").set_defaults(func=cmd_install_launcher)

    d = sub.add_parser("demo", help="print synthetic typing (no real data)")
    d.add_argument("-n", "--num", type=int, default=5)
    d.set_defaults(func=cmd_demo)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().print_help()
        return 0
    try:
        return args.func(args)
    except imgt.UpdateError as e:
        _err(f"Error: {e}")
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
