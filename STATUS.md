# STATUS

qtax — quarterly estimated tax estimator CLI
Asdale Dynamics, LLC — Copyright (c) 2026

## What was built

A local-first Python CLI for authors and small businesses to track income and
expense entries and estimate quarterly federal estimated tax. Everything runs
on the user's machine; there are no accounts, no API keys, and no network
access.

Components:
- `qtax/tax.py` — federal tax math for tax year 2026: marginal income tax
  brackets and standard deductions (IRS Rev. Proc. 2025-32 / IR-2025-103),
  self-employment tax (15.3% on 92.35% of net profit, Social Security wage base
  $184,500 per 2026 Form 1040-ES), and the quarterly estimated-payment
  estimate (income tax + SE tax, with the deductible employer-equivalent half
  of SE tax subtracted before income tax).
- `qtax/storage.py` — JSON storage file (default `~/.qtax/entries.json`,
  overridable via `--data-file` or `$QTAX_DATA_FILE`), atomic writes.
- `qtax/entries.py` — entry model (income/expense), add/list, totals, and
  year-to-date aggregation with a monthly breakdown.
- `qtax/export.py` — CSV export with stable column order.
- `qtax/cli.py` — argparse CLI: `add-income`, `add-expense`, `list`, `ytd`,
  `estimate`, `export`, `init`, plus `--version`.
- `qtax/__main__.py` — supports `python -m qtax`.
- `tests/` — pytest suite covering tax math, storage, entries, and CLI
  (44 tests).
- `LICENSE` — MIT, copyright line exactly
  `Copyright (c) 2026 Asdale Dynamics, LLC`.
- `README.md` — install, usage, command reference, worked example, tax notes,
  credits Asdale Dynamics, LLC, MIT license.

## How to run

Install (from the project folder):

```bash
pip install -e .
```

(Requires a virtualenv or `--break-system-packages` on PEP 668 systems.)

Commands:

```bash
qtax add-income 1200.00 --source KDP --note "book royalties"
qtax add-expense 49.99 --category software --note "AI coding tool"
qtax list
qtax ytd
qtax estimate 48000 --filing-status single
qtax export ledger.csv
qtax init
qtax --version
```

All commands accept `--data-file <path>`; default storage is
`~/.qtax/entries.json` or `$QTAX_DATA_FILE`.

Run tests:

```bash
python3 -m pytest
```

## Verification results

- `python3 -m pytest`: 44 passed, 0 failed
- `python3 -m ruff check qtax tests`: all checks passed
- End-to-end smoke test of `add-income`, `add-expense`, `list`, `ytd`,
  `estimate`, and `export` all ran successfully against a temp JSON file.
- Tax math verified against published IRS 2026 figures:
  - Single standard deduction $16,100; married filing jointly $32,200.
  - Top bracket 37% above $640,600 (single); base tax at the threshold is
    $192,979.25.
  - SE tax on $100,000 net profit = $14,129.55; full single-filer estimate
    yields total annual tax $25,745.30 and quarterly payment $6,436.33.

## Known gaps

- Only tax year 2026 is supported (other years raise ValueError).
- Federal-only estimate; no state tax, no credits/deductions beyond the
  standard deduction, no dependent or other adjustments.
- The SE deduction is applied as a flat 50% of SE tax (the Form 1040-ES
  worksheet approach), which is an approximation for planning purposes.
- `married_filing_jointly` uses double the single bracket thresholds and its
  own standard deduction; head of household and other statuses use the single
  bracket schedule with their own standard deduction (approximation).
- No interactive prompts, no GUI, no multi-user or encrypted storage.
- Not tax advice; users should verify with a tax professional before filing.

## Notes for Dylan Asdale / Asdale Dynamics, LLC

Built plain-English and beginner-friendly, with a worked example in the README
and a "this is an estimate, not tax advice" disclaimer throughout. Local-first
by design — no keys, no accounts, no network. Suitable as a template for the
LLC's small-business/author bookkeeping tools line.