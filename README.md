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

Each release lives in its own folder (`~/.local/share/hla-sero/releases/3.65.0/`)
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

## Development

```bash
./setup.sh                                            # .venv + editable install + tests
HLA_SERO_LIVE=1 .venv/bin/python -m pytest tests/test_live.py   # check the real release
```

```
src/hla_sero/
  wmda.py      parse the WMDA files
  engine.py    allele -> serology rules, text extraction
  imgt.py      download, checksum, cache, update policy
  cli.py       hla-sero command
  gui.py       local copy-paste server (127.0.0.1 only)
  web/index.html
tests/         offline tests (fixtures + fake GitHub) and an optional live test
```

Data: IPD-IMGT/HLA Database, https://www.ebi.ac.uk/ipd/imgt/hla/ — please cite
Barker DJ et al., *Nucleic Acids Research* (2023) and the WMDA files' README.
