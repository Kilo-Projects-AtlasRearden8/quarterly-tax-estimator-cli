"""Command-line interface for qtax.

Plain-English, local-first commands for tracking author/small-business
income and expenses and estimating quarterly federal estimated tax.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal, InvalidOperation

from . import __version__
from .entries import ENTRY_TYPES, list_entries, make_entry, ytd_totals
from .export import export_csv
from .storage import default_data_path, load_entries, save_entries
from .tax import (
    DEFAULT_TAX_YEAR,
    SUPPORTED_FILING_STATUSES,
    estimate_quarterly_tax,
)

EXIT_OK = 0
EXIT_ERROR = 1


def _amount(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"invalid amount: {value!r}") from exc


def _date(value: str) -> str:
    import datetime as dt

    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date (use YYYY-MM-DD): {value!r}") from exc
    return value


def _currency(value: Decimal) -> str:
    return f"${value:,.2f}"


def _status_hint(text: str) -> str:
    return text


def cmd_add(args: argparse.Namespace) -> int:
    path = args.data_file or default_data_path()
    entries = load_entries(path)
    entry = make_entry(
        entry_type=args.kind,
        amount=args.amount,
        date=args.date,
        note=args.note or "",
        source=getattr(args, "source", "") or "",
        category=getattr(args, "category", "") or "",
    )
    entry["id"] = max((int(e.get("id", 0)) for e in entries), default=0) + 1
    entries.append(entry)
    save_entries(path, entries)
    kind_label = args.kind.capitalize()
    print(f"Added {kind_label}: {_currency(Decimal(str(args.amount)))} on {entry['date']}")
    if entry["note"]:
        print(f"  Note: {entry['note']}")
    print(f"  Stored in: {path}")
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    path = args.data_file or default_data_path()
    entries = list_entries(path, entry_type=args.type)
    if not entries:
        print("No entries found.")
        print(f"Storage file: {path}")
        return EXIT_OK
    print(f"{'ID':<5} {'Type':<9} {'Amount':>12} {'Date':<11} Note")
    print("-" * 60)
    income = expense = Decimal("0")
    for entry in entries:
        amount = Decimal(str(entry.get("amount", 0)))
        if entry.get("type") == "income":
            income += amount
        else:
            expense += amount
        note = str(entry.get("note", ""))
        source = str(entry.get("source", ""))
        src = f" [{source}]" if source else ""
        print(
            f"{entry.get('id'):<5} {entry.get('type'):<9} "
            f"{amount:>12,.2f} {entry.get('date'):<11} {note}{src}"
        )
    print("-" * 60)
    print(f"{'TOTAL':<5} {'':<9} {income - expense:>12,.2f}")
    print(f"  Income: {_currency(income)}  Expense: {_currency(expense)}  Net: {_currency(income - expense)}")
    print(f"Storage file: {path}")
    return EXIT_OK


def cmd_ytd(args: argparse.Namespace) -> int:
    path = args.data_file or default_data_path()
    year = args.year or None
    summary = ytd_totals(path, year=year)
    label = summary["year"]
    print(f"Year-to-date for {label}")
    print("-" * 40)
    print(f"Entries:       {summary['entry_count']}")
    print(f"Income:        {_currency(Decimal(str(summary['income'])))}")
    print(f"Expense:       {_currency(Decimal(str(summary['expense'])))}")
    print(f"Net profit:    {_currency(Decimal(str(summary['net'])))}")
    if summary.get("by_month"):
        print()
        print("By month:")
        print(f"{'Month':<8} {'Income':>14} {'Expense':>14} {'Net':>14}")
        for month, bucket in summary["by_month"].items():
            print(
                f"{month:<8} "
                f"{Decimal(str(bucket['income'])):>14,.2f} "
                f"{Decimal(str(bucket['expense'])):>14,.2f} "
                f"{Decimal(str(bucket['net'])):>14,.2f}"
            )
    print()
    print("Tip: net profit is what feeds the quarterly tax estimate.")
    print(f"Storage file: {path}")
    return EXIT_OK


def _format_estimate(result) -> str:
    lines = []
    lines.append(f"Quarterly estimated tax estimate — tax year {result.tax_year}")
    lines.append("=" * 52)
    lines.append(f"Filing status:          {result.filing_status.replace('_', ' ').title()}")
    lines.append(f"Net business income:    {_currency(result.net_business_income)}")
    if result.other_income:
        lines.append(f"Other income:           {_currency(result.other_income)}")
    lines.append(f"Standard deduction:     {_currency(result.standard_deduction)}")
    lines.append(f"Taxable income:         {_currency(result.taxable_income)}")
    lines.append("")
    lines.append("Federal income tax:     " + _currency(result.income_tax))
    lines.append("Self-employment tax:    " + _currency(result.se_tax))
    lines.append("  (SE deduction taken:  " + _currency(result.se_deduction) + ")")
    lines.append("-" * 52)
    lines.append(f"Total annual tax:       {_currency(result.total_annual_tax)}")
    if result.withholding:
        lines.append(f"Withholding:            {_currency(result.withholding)}")
    lines.append(f"Balance due for year:   {_currency(result.balance_due)}")
    lines.append("")
    if result.owes_estimated_tax:
        lines.append(f"Quarterly payment:      {_currency(result.quarterly_payment)} x 4")
        lines.append("Due dates: " + ", ".join(
            __import__("qtax.tax", fromlist=["QUARTERLY_DUE_DATES"]).QUARTERLY_DUE_DATES
        ))
        lines.append("")
        lines.append("You likely owe estimated tax (you expect to owe $1,000 or more).")
    else:
        lines.append("Quarterly payment:      $0.00")
        lines.append("")
        lines.append("You likely do not need to make estimated payments (you expect to")
        lines.append("owe less than $1,000 for the year).")
    lines.append("")
    lines.append("This is an estimate, not tax advice. Talk with a tax professional.")
    return "\n".join(lines)


def cmd_estimate(args: argparse.Namespace) -> int:
    try:
        result = estimate_quarterly_tax(
            net_business_income=args.net_profit,
            other_income=args.other_income,
            withholding=args.withholding,
            filing_status=args.filing_status,
            tax_year=args.tax_year,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return EXIT_ERROR
    print(_format_estimate(result))
    return EXIT_OK


def cmd_export(args: argparse.Namespace) -> int:
    path = args.data_file or default_data_path()
    entries = load_entries(path)
    export_csv(args.output, entries)
    print(f"Exported {len(entries)} entries to {args.output}")
    print(f"Source storage file: {path}")
    return EXIT_OK


def cmd_init(args: argparse.Namespace) -> int:
    path = args.data_file or default_data_path()
    if os.path.exists(path):
        print(f"Storage file already exists: {path}")
        return EXIT_OK
    save_entries(path, [])
    print(f"Created empty storage file: {path}")
    return EXIT_OK


import os  # noqa: E402 (placed after heavy imports for clarity)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qtax",
        description=(
            "Local-first CLI for authors and small businesses: track income "
            "and expenses, then estimate quarterly federal estimated tax. "
            "No accounts, no keys, no network."
        ),
    )
    parser.add_argument("--version", action="version", version=f"qtax {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    add_parent = argparse.ArgumentParser(add_help=False)
    add_parent.add_argument("amount", type=_amount, help="dollar amount, e.g. 500.00")
    add_parent.add_argument("--date", type=_date, help="entry date YYYY-MM-DD (default: today)")
    add_parent.add_argument("--note", default="", help="short note")
    add_parent.add_argument(
        "--data-file",
        help="path to the JSON storage file",
    )

    p_add_income = sub.add_parser(
        "add-income", parents=[add_parent], help="record an income entry"
    )
    p_add_income.add_argument("--source", default="", help="income source (client, platform, etc.)")
    p_add_income.set_defaults(kind="income", func=cmd_add)

    p_add_expense = sub.add_parser(
        "add-expense", parents=[add_parent], help="record an expense entry"
    )
    p_add_expense.add_argument("--category", default="", help="expense category")
    p_add_expense.set_defaults(kind="expense", func=cmd_add)

    p_list = sub.add_parser("list", help="list entries, newest first")
    p_list.add_argument("--type", choices=ENTRY_TYPES, help="filter by income or expense")
    p_list.add_argument("--data-file", help="path to the JSON storage file")
    p_list.set_defaults(func=cmd_list)

    p_ytd = sub.add_parser("ytd", help="year-to-date income/expense totals")
    p_ytd.add_argument("--year", type=int, help="year to summarize (default: current year)")
    p_ytd.add_argument("--data-file", help="path to the JSON storage file")
    p_ytd.set_defaults(func=cmd_ytd)

    p_est = sub.add_parser(
        "estimate", help="estimate quarterly federal estimated tax"
    )
    p_est.add_argument("net_profit", type=_amount, help="expected net business profit for the year")
    p_est.add_argument(
        "--other-income", type=_amount, default=Decimal("0"),
        help="other expected income (wages, interest, etc.)",
    )
    p_est.add_argument(
        "--withholding", type=_amount, default=Decimal("0"),
        help="federal tax already withheld for the year",
    )
    p_est.add_argument(
        "--filing-status",
        choices=SUPPORTED_FILING_STATUSES,
        default="single",
        help="filing status (default: single)",
    )
    p_est.add_argument(
        "--tax-year", type=int, default=DEFAULT_TAX_YEAR,
        help=f"tax year (default: {DEFAULT_TAX_YEAR})",
    )
    p_est.add_argument(
        "--data-file", help="path to the JSON storage file"
    )
    p_est.set_defaults(func=cmd_estimate)

    p_export = sub.add_parser("export", help="export entries to CSV")
    p_export.add_argument("output", help="path for the output CSV file")
    p_export.add_argument("--data-file", help="path to the JSON storage file")
    p_export.set_defaults(func=cmd_export)

    p_init = sub.add_parser("init", help="create an empty storage file")
    p_init.add_argument("--data-file", help="path to the JSON storage file")
    p_init.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
