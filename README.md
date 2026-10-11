# HLA Serologic Converter (`hla-sero`)

Converts molecular HLA typing into serological equivalents using the
**current IPD-IMGT/HLA release**, downloaded straight from the official
[ANHIG/IMGTHLA](https://github.com/ANHIG/IMGTHLA) repository and kept up to date
automatically.

Paste typing in any layout — a block copied from Excel, a report line, a list —
and get the antigen, broad and associated antigen for every allele, with a
per-sample summary ready to copy.

```
SYN0001  A*02:01  A*24:02  B*15:01  B*15:03  C*03:04  DRB1*03:01
   ->    A2       A24      B62      B72      Cw10     DR17
 broad   A2       A9       B15      B70      Cw3      DR3
```

> Runs locally. Pasted typing never leaves the computer; the only network
> traffic is the IMGT/HLA update check to GitHub. A tool for checking typing
> data — results need review before clinical use.

## Windows (lab PCs) — no installation

Download **`hla-sero.exe`** from the [Releases](../../releases) page and double-click it.
No Python, no admin rights. Built and smoke-tested on Windows by GitHub Actions;
every release lists its SHA256.
Lab guide in Korean: [`docs/LAB_WINDOWS_KO.md`](docs/LAB_WINDOWS_KO.md)

## Install (Linux Mint / Ubuntu)

```bash
git clone https://github.com/bluebut11-EO/hla-serologic-converter.git
cd hla-serologic-converter
./install.sh
```

This installs the `hla-sero` command (via `pipx`), downloads the latest
IMGT/HLA release and adds **HLA Serology Converter** to the menu.

Step-by-step guide in Korean: [`docs/SETUP_LINUX_MINT_KO.md`](docs/SETUP_LINUX_MINT_KO.md)

## Use

| | |
|---|---|
| `hla-sero gui` | copy-paste window in the browser (also in the menu) |
| `hla-sero convert` | paste in the terminal, finish with Ctrl+D |
| `hla-sero convert typing.txt -o result.csv` | convert a file |
| `hla-sero status` | release in use, update settings |
| `hla-sero update` | check for a new release now |
| `hla-sero config --pin 3.64.0` / `--unpin` | lock to a validated release / follow latest |
| `hla-sero config --auto-update notify` | `auto` (default), `notify`, or `off` |
| `hla-sero diff 3.64.0 3.65.0` | what changed between two releases |

## Cross-check against your current serology

Put the serology you already use after each allele — in Excel columns
(`Sample | Allele | Serology`) or inline (`A*02:01 A2  B*15:03 B72`) — and each row is
marked **match**, **broad-match** (you entered the broad, e.g. A9 for A24) or
**mismatch**. Legacy associated names such as `A203` match the 2026 names (`A0203`).
In delimited data only the cell right after the allele is read, so comment columns are
safe. A worksheet of difficult alleles to fill in: [`docs/cross_check_template.csv`](docs/cross_check_template.csv)

## Where the answers come from

Four WMDA files published with every IMGT/HLA release:

| File | Used for |
|---|---|
| `rel_dna_ser.txt` | allele → serological code (unambiguous / possible / assumed / HATS) |
| `rel_ser_ser.txt` | associated antigen → antigen → broad (e.g. B1501 → B62 → B15) |
| `hla_nom_g.txt`, `hla_nom_p.txt` | expanding G and P groups |

Rules:

- **mapped** only when serology is characterised (WMDA unambiguous/possible).
- **assumed** when WMDA only infers it from the allele name — always flagged.
- **ambiguous** when the alleles a typing covers map to different antigens
  (e.g. `B*15` or `B*15:01/15:03`) — every candidate is listed, none is chosen.
- Two-field, G/P and XX typings exclude null/questionable (N/Q) members; the
  count is shown. An explicit null allele is reported as **null**.
- Every result carries the release it came from.

### Updates

Each release lives in its own folder (`~/.local/share/hla-sero/releases/3.65.0/`;
on Windows `%LOCALAPPDATA%\hla-sero\releases\`)
and is never overwritten. Downloads are verified against IMGT/HLA's published
md5 checksums. In `auto` mode the app checks GitHub at most once a week and
switches to a newer release; older releases stay installed so you can pin one.

### Lab policy overrides (optional)

Where your lab or a registry (e.g. OPTN/UNOS equivalency tables) differs from
WMDA, put exceptions in `~/.config/hla-sero/overrides.csv`:

```
allele,equivalent,associated,broad,note
A*02:03,A203,,A2,UNOS listing
```

## Release watch and email alerts

`.github/workflows/imgt-watch.yml` checks IPD-IMGT/HLA every Monday. When a new
release appears it opens one issue listing every 2-field group whose serological
equivalent or status changed since the previous release, and whether hla-sero's
checks pass against it — GitHub emails you about the issue. The same comparison
locally:

```bash
hla-sero diff 3.64.0 3.65.0            # or -o changes.md for a Markdown report
```

Setup and what to do when an alert arrives (Korean): [`docs/EMAIL_ALERTS_KO.md`](docs/EMAIL_ALERTS_KO.md)

## Building the Windows program

`.github/workflows/build.yml` runs the tests on Linux and Windows (plus a live check
against the current IMGT/HLA release), builds `hla-sero.exe` with PyInstaller and
smoke-tests it. Every run keeps the exe as a downloadable artifact; pushing a tag
publishes a release:

```bash
git tag v0.3.0 && git push origin v0.3.0
```

## Development

```bash
./setup.sh                                            # .venv + editable install + tests
HLA_SERO_LIVE=1 .venv/bin/python -m pytest tests/test_live.py   # check the real release
```

```
src/hla_sero/
  wmda.py      parse the WMDA files
  engine.py    allele -> serology rules, text extraction
  crosscheck.py  compare with the lab's existing serology
  diff.py      release-to-release changes
  imgt.py      download, checksum, cache, update policy
  cli.py       hla-sero command
  gui.py       local copy-paste server (127.0.0.1 only)
  web/index.html
packaging/     Windows exe entry point, weekly watch script
tests/         offline tests (fixtures + fake GitHub) and an optional live test
```

## Licence

- **hla-sero code:** [MIT](LICENSE) — free to use, modify and share; provided "as is", without warranty.
- **IMGT/HLA data:** not included in this repository. hla-sero downloads the unmodified WMDA
  files from the official [ANHIG/IMGTHLA](https://github.com/ANHIG/IMGTHLA) repository, which are
  © IPD-IMGT/HLA under the Creative Commons Attribution-NoDerivs licence
  ([LICENCE.md](https://github.com/ANHIG/IMGTHLA/blob/Latest/LICENCE.md)). Distributing a
  *modified* version of that data needs permission from the IPD team. The test fixtures in
  `tests/conftest.py` are synthetic and are not IMGT/HLA data.

When you use results from hla-sero, please cite the IPD-IMGT/HLA Database:

- Barker DJ, Natarajan RHL, Cooper MA, Hopper SJF, Yates AD, Parham P, Marsh SGE, Robinson J.
  The IPD-IMGT/HLA Database: recent developments in sequence submission.
  *Nucleic Acids Research* (2026) 54(D1): D1152–D1158
- Robinson J, Barker D, Marsh SGE. 25 years of the IPD-IMGT/HLA Database. *HLA* (2024) 103(6): e15549

IPD-IMGT/HLA asks commercial users of its data to consider funding the database (see its LICENCE.md).
