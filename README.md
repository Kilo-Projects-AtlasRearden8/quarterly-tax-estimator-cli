# qtax

A local-first CLI for authors and small businesses to **estimate quarterly
federal estimated taxes** from your own income and expense entries.

Built by **Asdale Dynamics, LLC**. It stores entries in a JSON file on your
machine, exports CSV, computes year-to-date totals, and estimates your
quarterly payments using published IRS figures. No accounts, no API keys, no
network. Your money data never leaves your computer.

> This is an estimator, not tax advice. It is designed to help you plan and
> talk to a tax professional with confidence. Always verify with a qualified
> preparer before filing.

## Features

- **JSON storage** — every entry lives in one file (default `~/.qtax/entries.json`).
  Override with `--data-file` or the `QTAX_DATA_FILE` environment variable.
- **Income and expense entries** — track royalties, client work, software, ads, and more.
- **Year-to-date totals** — monthly breakdowns of income, expense, and net profit.
- **CSV export** — share your ledger with a spreadsheet or your accountant.
- **Quarterly estimated tax estimate** — federal income tax + self-employment tax,
  with the deductible employer-equivalent SE tax subtracted before income tax,
  mirroring the IRS Form 1040-ES worksheet.
- **Tax year 2026 figures** — brackets and standard deductions from IRS Revenue
  Procedure 2025-32; Social Security wage base from the 2026 Form 1040-ES.

## Install

```bash
pip install -e .
```

This installs the `qtax` command and the `qtax` Python package.

## Quick start

```bash
# Record income and expenses
qtax add-income 1200.00 --source "KDP" --note "The Massive AI Manual royalties"
qtax add-expense 49.99 --category "software" --note "AI coding tool"

# See what you've got so far
qtax list
qtax ytd

# Estimate quarterly payments
qtax estimate 48000

# Export your ledger
qtax export ledger.csv
```

## Commands

| Command | What it does |
| --- | --- |
| `qtax add-income <amount>` | Record an income entry |
| `qtax add-expense <amount>` | Record an expense entry |
| `qtax list [--type income\|expense]` | List entries, newest first, with totals |
| `qtax ytd [--year YYYY]` | Year-to-date totals with a monthly breakdown |
| `qtax estimate <net-profit>` | Estimate quarterly federal estimated tax |
| `qtax export <file.csv>` | Export entries to CSV |
| `qtax init` | Create an empty storage file |

All commands accept `--data-file <path>` to point at a specific storage file.
The default path is `~/.qtax/entries.json`, or `$QTAX_DATA_FILE` if set.

## Estimate example

```text
$ qtax estimate 100000
Quarterly estimated tax estimate — tax year 2026
====================================================
Filing status:          Single
Net business income:    $100,000.00
Standard deduction:     $16,100.00
Taxable income:          $76,835.22

Federal income tax:      $11,623.75
Self-employment tax:     $14,129.55
  (SE deduction taken:   $7,064.78)
----------------------------------------------------
Total annual tax:        $25,745.30
Balance due for year:    $25,745.30

Quarterly payment:       $6,436.33 x 4
Due dates: April 15, June 15, September 15, January 15 (following year)

You likely owe estimated tax (you expect to owe $1,000 or more).
```

## Tax math notes

- Self-employment tax is `15.3%` on `92.35%` of net profit, with Social Security
  tax capped at the 2026 wage base (`$184,500`) and Medicare uncapped.
- Half of the SE tax is deducted before figuring income tax.
- Estimated payments are required when the expected balance due is `$1,000` or more.
- Brackets are the 2026 single-filer schedule; `married_filing_jointly` uses
  double the single thresholds and standard deduction.

## Running tests

```bash
pip install pytest
pytest
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.