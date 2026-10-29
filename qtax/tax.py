"""Federal tax math for quarterly estimated tax.

All figures are for tax year 2026, sourced from IRS Revenue Procedure
2025-32 (IR-2025-103) and the 2026 Form 1040-ES. This is an estimator,
not professional tax advice. Verify with a tax professional before filing.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Self-employment tax (IRS: 15.3% = 12.4% Social Security + 2.9% Medicare).
SE_TAX_RATE = Decimal("0.153")
SS_TAX_RATE = Decimal("0.124")
MEDICARE_TAX_RATE = Decimal("0.029")
# Only 92.35% of net self-employment earnings are subject to SE tax.
SE_EARNINGS_FACTOR = Decimal("0.9235")
# Employer-equivalent half of SE tax is deductible for income tax.
SE_DEDUCTION_FACTOR = Decimal("0.50")
# 2026 Social Security wage base (2026 Form 1040-ES).
SS_WAGE_BASE_2026 = Decimal("184500.00")

# Estimated tax is generally required when you expect to owe at least $1,000.
ESTIMATED_TAX_THRESHOLD = Decimal("1000.00")

# 2026 quarterly estimated tax due dates (calendar year filers).
QUARTERLY_DUE_DATES = (
    "April 15",
    "June 15",
    "September 15",
    "January 15 (following year)",
)


@dataclass(frozen=True)
class BracketTable:
    """Marginal bracket table: (lower bound, rate, base tax at lower bound)."""

    brackets: tuple[tuple[Decimal, Decimal, Decimal], ...]
    standard_deduction: Decimal


# Tax year 2026 marginal rate schedules (IRS Rev. Proc. 2025-32).
# Each entry: taxable income over this amount -> rate, plus base tax.
_BRACKETS_2026: dict[str, tuple[tuple[Decimal, Decimal, Decimal], ...]] = {
    "single": (
        (Decimal("0"), Decimal("0.10"), Decimal("0")),
        (Decimal("12400"), Decimal("0.12"), Decimal("1240.00")),
        (Decimal("50400"), Decimal("0.22"), Decimal("5800.00")),
        (Decimal("105700"), Decimal("0.24"), Decimal("17966.00")),
        (Decimal("201775"), Decimal("0.32"), Decimal("41024.00")),
        (Decimal("256225"), Decimal("0.35"), Decimal("58448.00")),
        (Decimal("640600"), Decimal("0.37"), Decimal("192989.25")),
    ),
}
_BRACKETS_2026["married_filing_jointly"] = tuple(
    (low * 2, rate, base * 2)
    for low, rate, base in _BRACKETS_2026["single"]
)

_STANDARD_DEDUCTION_2026 = {
    "single": Decimal("16100.00"),
    "married_filing_separately": Decimal("16100.00"),
    "married_filing_jointly": Decimal("32200.00"),
    "surviving_spouse": Decimal("32200.00"),
    "head_of_household": Decimal("24150.00"),
}

SUPPORTED_FILING_STATUSES = (
    "single",
    "married_filing_jointly",
    "married_filing_separately",
    "surviving_spouse",
    "head_of_household",
)

DEFAULT_TAX_YEAR = 2026


def _money(value: Decimal) -> Decimal:
    """Round a Decimal to whole cents."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def bracket_table(filing_status: str, tax_year: int = DEFAULT_TAX_YEAR) -> BracketTable:
    """Return the bracket table and standard deduction for a filing status."""
    if tax_year != DEFAULT_TAX_YEAR:
        raise ValueError(f"only tax year {DEFAULT_TAX_YEAR} is supported")
    status = filing_status.lower().replace(" ", "_").replace("-", "_")
    if status not in _BRACKETS_2026:
        # head_of_household and surviving_spouse use the single bracket
        # schedule with their own standard deduction (approximation).
        status = "single"
    try:
        standard = _STANDARD_DEDUCTION_2026[status]
    except KeyError:
        standard = _STANDARD_DEDUCTION_2026["single"]
    return BracketTable(brackets=_BRACKETS_2026[status], standard_deduction=standard)


def federal_income_tax(
    taxable_income: Decimal, filing_status: str = "single", tax_year: int = DEFAULT_TAX_YEAR
) -> Decimal:
    """Federal income tax on already-computed taxable income (post-deduction)."""
    if taxable_income <= 0:
        return Decimal("0.00")
    table = bracket_table(filing_status, tax_year)
    tax = Decimal("0.00")
    for lower, rate, base in table.brackets:
        if taxable_income <= lower:
            break
        tax = base + (taxable_income - lower) * rate
    return _money(tax)


def self_employment_tax(
    net_profit: Decimal, tax_year: int = DEFAULT_TAX_YEAR
) -> dict[str, Decimal]:
    """Self-employment tax on net self-employment profit.

    Returns the SE tax, the deductible employer-equivalent half, and the
    earnings amount actually subject to SE tax (92.35% of net profit).
    """
    if tax_year != DEFAULT_TAX_YEAR:
        raise ValueError(f"only tax year {DEFAULT_TAX_YEAR} is supported")
    taxable_se = _money(max(Decimal("0"), net_profit) * SE_EARNINGS_FACTOR)
    ss_wage = min(taxable_se, SS_WAGE_BASE_2026)
    ss_tax = _money(ss_wage * SS_TAX_RATE)
    medicare_tax = _money(taxable_se * MEDICARE_TAX_RATE)
    se_tax = _money(ss_tax + medicare_tax)
    return {
        "taxable_se_earnings": _money(taxable_se),
        "social_security_tax": ss_tax,
        "medicare_tax": medicare_tax,
        "self_employment_tax": se_tax,
        "deductible_portion": _money(se_tax * SE_DEDUCTION_FACTOR),
    }


@dataclass
class EstimateResult:
    tax_year: int
    filing_status: str
    net_business_income: Decimal
    other_income: Decimal
    standard_deduction: Decimal
    se_tax: Decimal
    se_deduction: Decimal
    taxable_income: Decimal
    income_tax: Decimal
    total_annual_tax: Decimal
    withholding: Decimal
    balance_due: Decimal
    quarterly_payment: Decimal
    owes_estimated_tax: bool


def estimate_quarterly_tax(
    net_business_income: Decimal,
    *,
    other_income: Decimal = Decimal("0"),
    withholding: Decimal = Decimal("0"),
    filing_status: str = "single",
    tax_year: int = DEFAULT_TAX_YEAR,
) -> EstimateResult:
    """Estimate annual tax and the quarterly estimated payment.

    Self-employment tax is computed on net business income. Half of SE tax
    is subtracted before figuring income tax, mirroring the Form 1040-ES
    Self-Employment Tax and Deduction Worksheet.
    """
    if tax_year != DEFAULT_TAX_YEAR:
        raise ValueError(f"only tax year {DEFAULT_TAX_YEAR} is supported")

    se = self_employment_tax(net_business_income, tax_year)
    table = bracket_table(filing_status, tax_year)

    adjusted_business_income = max(
        Decimal("0"), net_business_income - se["deductible_portion"]
    )
    taxable_income = max(
        Decimal("0"),
        adjusted_business_income + max(Decimal("0"), other_income) - table.standard_deduction,
    )
    income_tax = federal_income_tax(taxable_income, filing_status, tax_year)

    total_annual_tax = _money(income_tax + se["self_employment_tax"])
    balance_due = _money(total_annual_tax - max(Decimal("0"), withholding))
    owes = balance_due >= ESTIMATED_TAX_THRESHOLD
    quarterly_payment = _money(balance_due / 4) if owes else Decimal("0.00")

    return EstimateResult(
        tax_year=tax_year,
        filing_status=filing_status,
        net_business_income=_money(net_business_income),
        other_income=_money(other_income),
        standard_deduction=table.standard_deduction,
        se_tax=se["self_employment_tax"],
        se_deduction=se["deductible_portion"],
        taxable_income=_money(taxable_income),
        income_tax=income_tax,
        total_annual_tax=total_annual_tax,
        withholding=_money(withholding),
        balance_due=balance_due,
        quarterly_payment=quarterly_payment,
        owes_estimated_tax=owes,
    )
