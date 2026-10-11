"""
imgt_watch.py — weekly check used by .github/workflows/imgt-watch.yml

  python packaging/imgt_watch.py --out report.md [--tests live.txt] [--tests-outcome success]

1. reads the newest IPD-IMGT/HLA release from the IMGTHLA "Latest" branch
2. finds the release before it among the per-release branches (3650, 3640 ...)
3. downloads both (md5-verified) and compares every 2-field serology group
4. writes a Markdown report and, under GitHub Actions, the outputs
   version / previous / changed for the workflow's issue step
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from hla_sero import __version__, imgt, wmda
from hla_sero.diff import release_diff, render_markdown

IMGT_GIT = "https://github.com/ANHIG/IMGTHLA.git"


def branch_to_version(branch: str) -> str | None:
    """'3650' -> '3.65.0'   (IMGTHLA names one branch per release this way)"""
    if not re.fullmatch(r"\d{3,6}", branch):
        return None
    return f"{branch[0]}.{int(branch[1:-1])}.{branch[-1]}"


def release_versions() -> list[str]:
    out = subprocess.run(["git", "ls-remote", "--heads", IMGT_GIT],
                         capture_output=True, text=True, check=True, timeout=120).stdout
    names = [line.split("refs/heads/")[-1] for line in out.splitlines()]
    versions = {v for v in map(branch_to_version, names) if v}
    return sorted(versions, key=imgt._version_key)


def build_report(tests_text: str = "", tests_outcome: str = "") -> tuple[dict, str]:
    latest = imgt.remote_version("Latest")
    older = [v for v in release_versions() if imgt._version_key(v) < imgt._version_key(latest)]
    previous = older[-1] if older else None

    log = lambda m: print(m, file=sys.stderr)   # noqa: E731
    new_v = imgt.download_release("Latest", log=log)
    new_db = wmda.load(imgt.releases_dir() / new_v)

    parts = [f"Weekly check by hla-sero {__version__} found **IPD-IMGT/HLA {new_v}** "
             f"(file date {new_db.date}).", ""]
    info = {"version": new_v, "previous": previous or "", "changed": "0"}

    if previous:
        old_v = imgt.download_release(imgt.release_to_ref(previous), log=log)
        d = release_diff(wmda.load(imgt.releases_dir() / old_v), new_db)
        info["changed"] = str(len(d.changed))
        parts.append(render_markdown(d))
    else:
        parts.append("_No earlier release branch found to compare with._")

    if tests_outcome:
        ok = tests_outcome == "success"
        parts += ["", f"### hla-sero checks against {new_v}: {'✅ passed' if ok else '❌ FAILED'}", ""]
        if tests_text.strip():
            tail = "\n".join(tests_text.strip().splitlines()[-40:])
            parts += ["```", tail, "```"]
        if not ok:
            parts += ["", "**Do not move the lab PCs to this release** until hla-sero is fixed "
                      "(keep them pinned to the current release)."]

    parts += ["", "### Before using this release in the lab",
              "1. Run the validation set (`docs/cross_check_template.csv`) on the new release and save the CSV.",
              "2. Review every row in *Changed* above.",
              "3. Only then un-pin / pin the new release on the lab PCs.",
              "", f"_Source: https://github.com/ANHIG/IMGTHLA — compared with the {previous or 'n/a'} release branch._"]
    return info, "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tests", help="file with the live test output")
    ap.add_argument("--tests-outcome", default="", help="success / failure from the test step")
    args = ap.parse_args()

    os.environ.setdefault("HLA_SERO_HOME", tempfile.mkdtemp(prefix="hla-sero-watch-"))
    tests_text = Path(args.tests).read_text(errors="replace") if args.tests and Path(args.tests).exists() else ""
    info, report = build_report(tests_text, args.tests_outcome)
    Path(args.out).write_text(report, encoding="utf-8")
    if gh_out := os.environ.get("GITHUB_OUTPUT"):          # write outputs before anything else can fail
        with open(gh_out, "a", encoding="utf-8") as fh:
            for k, v in info.items():
                fh.write(f"{k}={v}\n")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
