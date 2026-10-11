# HLA Molecular → Serologic Equivalent Converter

A small, readable tool that converts molecular HLA typing (IMGT/HLA allele
format, e.g. `A*24:02`) into UNOS **serologic** antigen equivalents
(e.g. `A24`, broad `A9`). This is the **logic layer** between molecular typing
and the serologic vocabulary a **virtual crossmatch (vXM)** is expressed in.

> ⚠️ **Synthetic data only.** Everything here uses fake, generated typings.
> No PHI, ever. The synthetic generator never touches real records.

> ⚠️ **The reference table is an illustrative SUBSET, not production-ready.**
> It maps at the allele-*family* level as a teaching simplification. The
> authoritative source is IMGT/HLA's `rel_dna_ser.txt`, which assigns serology
> per *allele* (some alleles in a family differ, or have null/expert
> assignments). Swapping that file in is the first "graduation" TODO.

## Why this project

It sits exactly on the seam between domain expertise and code: only someone who
knows HLA can tell whether the output is *correct*, and the computational parts
(parsing, normalization, table joins, tests) are the skills being built. Good
for both an internal lab transition and an external bioinformatics-scientist
move — and it scales up into a master's capstone.

## Structure

```
hla-serologic-converter/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── reference/serologic_equivalents.csv   # the mapping table (subset)
│   └── synthetic/                            # generated fake typings land here
├── src/
│   ├── converter.py          # core: normalize allele + lookup (stdlib only)
│   ├── generate_synthetic.py # make fake donor typings (no PHI)
│   └── cli.py                # convert a typing CSV (pandas layer)
└── tests/
    └── test_converter.py     # runs with or without pytest
```

## Quickstart

**Linux Mint / Ubuntu (recommended):**

```bash
chmod +x setup.sh run.sh
./setup.sh      # one-time: creates .venv, installs deps, runs tests
./run.sh        # synthetic data -> conversion -> summary
```

Full step-by-step guide (Korean), including GitHub SSH setup:
[`docs/SETUP_LINUX_MINT_KO.md`](docs/SETUP_LINUX_MINT_KO.md)

**Manual:**

```bash
# 1. (optional) virtual env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. run the tests
python -m tests.test_converter        # no pytest needed
# pytest                              # also works if installed

# 3. generate synthetic typings, then convert them
python -m src.generate_synthetic -n 20
python -m src.cli

# 4. convert a single allele
python -m src.cli --allele "DRB1*15:01"
# -> DRB1*15:01 -> DR15 (broad DR2)
```

## 2-week learning roadmap

Built for ~30 min on weekdays + a longer weekend block. Each task maps to a
real piece of this repo, so you learn by extending working code rather than
reading tutorials.

### Week 1 — computing foundations on familiar ground
- **Day 1 — Git + run it.** Init a repo, make your first commit, push to a
  private GitHub repo. Run the tests; read `converter.py` top to bottom.
- **Day 2 — Read the parser.** Study `normalize_allele`. Add one test case for
  an allele with an expression suffix (e.g. `A*24:09N`). Watch it pass.
- **Day 3 — Break it on purpose.** Feed the converter a malformed allele from a
  real edge case you've seen at the bench. Make the parser handle it; commit.
- **Day 4 — Command line.** From a terminal: `grep`, `wc -l`, and a pipe to
  count how many `unmapped` cells appear in `sample_converted.csv`.
- **Weekend — Extend the reference table.** Add 5–10 allele families you know
  cold (with correct split/broad). Add matching tests. This is the part where
  your domain knowledge writes the code.

### Week 2 — the bioinformatics + pandas layer
- **Day 5 — pandas basics.** In `cli.py`, read the synthetic CSV into a
  DataFrame; print value counts of `_status` columns.
- **Day 6 — Reshape.** Convert the wide table to long format
  (`sample_id, locus, allele`) with `pd.melt`; re-run the conversion on it.
- **Day 7 — A real format.** Learn the VCF spec at a glance; write a 10-line
  function that reads the sample IDs out of a tiny VCF header. (You don't need
  the whole file yet — just see the format.)
- **Day 8 — Reproducibility.** Add a `make`-style script (or a `run.sh`) that
  regenerates data → converts → tests in one command. This "one command
  reproduces everything" habit is a strong clinical-lab signal.
- **Weekend — Swap in real reference data.** Download IMGT/HLA `rel_dna_ser.txt`,
  re-key the table from family to full allele, and handle the null/expert flags.
  This is the leap from toy to credible.

## Authoritative data sources (for the graduation step)
- **IMGT/HLA** `rel_dna_ser.txt` — allele-level serologic assignments.
- **NMDP / WMDA `py-ard`** — Python library for ARD reduction and resolution
  conversion; the natural next dependency.
- **UNOS / OPTN** antigen equivalency tables — the serologic vocabulary used in
  allocation and unacceptable-antigen listing.

## Roadmap beyond the basics
- Replace family-level table with allele-level `rel_dna_ser` (+ `py-ard`).
- Take a recipient unacceptable-antigen list + a donor typing → vXM call.
- Thin web UI (you already have the Netlify/single-file skill) to demo it.
