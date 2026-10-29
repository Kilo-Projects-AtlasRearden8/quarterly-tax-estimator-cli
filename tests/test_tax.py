"""Tests for the tax math module (tests/test_tax.py)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from qtax.tax import (
    ESTIMATED_TAX_THRESHOLD,
    SS_WAGE_BASE_2026,
    bracket_table,
    estimate_quarterly_tax,
    federal_income_tax,
    self_employment_tax,
)


def test_standard_deduction_2026_single():
    table = bracket_table("single")
    assert table.standard_deduction == Decimal("16100.00")


def test_standard_deduction_2026_mfj():
    table = bracket_table("married_filing_jointly")
    assert table.standard_deduction == Decimal("32200.00")


def test_federal_income_tax_zero():
    assert federal_income_tax(Decimal("0")) == Decimal("0.00")
    assert federal_income_tax(Decimal("-500")) == Decimal("0.00")


def test_federal_income_tax_10_percent_bracket():
    # $12,400 * 10% = $1,240
    assert federal_income_tax(Decimal("12400")) == Decimal("1240.00")


def test_federal_income_tax_12_percent_bracket():
    # $12,400 base + ($50,400 - $12,400) * 12% = $1,240 + $4,560 = $5,800
    assert federal_income_tax(Decimal("50400")) == Decimal("5800.00")


def test_federal_income_tax_22_percent_bracket():
    # $5,800 + ($60,000 - $50,400) * 22% = $5,800 + $2,112 = $7,912
    assert federal_income_tax(Decimal("60000")) == Decimal("7912.00")


def test_federal_income_tax_top_bracket_single():
    # $640,600: base $192,979.25 exactly at the 37% threshold
    assert federal_income_tax(Decimal("640600")) == Decimal("192979.25")


def test_federal_income_tax_mfj_brackets_are_double_single():
    single = federal_income_tax(Decimal("60000"), filing_status="single")
    mfj = federal_income_tax(Decimal("120000"), filing_status="married_filing_jointly")
    assert mfj == single * 2


def test_self_employment_tax_basic():
    # 92.35% of $100,000 = $92,350; SS $11,451.40 + Medicare $2,678.15
    result = self_employment_tax(Decimal("100000"))
    assert result["taxable_se_earnings"] == Decimal("92350.00")
    assert result["social_security_tax"] == Decimal("11451.40")
    assert result["medicare_tax"] == Decimal("2678.15")
    assert result["self_employment_tax"] == Decimal("14129.55")
    assert result["deductible_portion"] == Decimal("7064.78")


def test_self_employment_tax_wage_base_cap():
    # Earnings above the $184,500 wage base stop accruing Social Security tax.
    result = self_employment_tax(Decimal("300000"))
    taxable_se = Decimal("300000") * Decimal("0.9235")  # 277,050
    ss_tax = SS_WAGE_BASE_2026 * Decimal("0.124")  # capped
    medicare = taxable_se * Decimal("0.029")
    expected = _round(ss_tax + medicare)
    assert result["social_security_tax"] == _round(ss_tax)
    assert result["medicare_tax"] == _round(medicare)
    assert result["self_employment_tax"] == expected


def test_self_employment_tax_no_negative():
    assert self_employment_tax(Decimal("-1000"))["self_employment_tax"] == Decimal("0.00")


def test_estimate_no_tax_due_below_threshold():
    result = estimate_quarterly_tax(
        Decimal("5000"), filing_status="single", withholding=Decimal("0")
    )
    assert not result.owes_estimated_tax
    assert result.quarterly_payment == Decimal("0.00")


def test_estimate_full_calculation_single():
    # Net profit $100,000, single, no withholding.
    result = estimate_quarterly_tax(
        Decimal("100000"), filing_status="single", withholding=Decimal("0")
    )
    assert result.se_tax == Decimal("14129.55")
    assert result.se_deduction == Decimal("7064.78")
    # Taxable income: 100,000 - 7,064.78 - 16,100 = 76,835.22
    assert result.taxable_income == Decimal("76835.22")
    # Income tax: 5,800 + (76,835.22 - 50,400) * 22% = 11,615.75
    assert result.income_tax == Decimal("11615.75")
    assert result.total_annual_tax == Decimal("25745.30")
    assert result.balance_due == Decimal("25745.30")
    assert result.owes_estimated_tax is True
    assert result.quarterly_payment == Decimal("6436.33")


def test_estimate_with_withholding():
    result = estimate_quarterly_tax(
        Decimal("100000"),
        filing_status="single",
        withholding=Decimal("25000"),
    )
    assert result.balance_due == Decimal("745.30")
    assert not result.owes_estimated_tax
    assert result.quarterly_payment == Decimal("0.00")


def test_estimate_mfj():
    result = estimate_quarterly_tax(
        Decimal("100000"), filing_status="married_filing_jointly"
    )
    # MFJ standard deduction $32,200; lower taxable income => lower tax
    single_result = estimate_quarterly_tax(Decimal("100000"), filing_status="single")
    assert result.income_tax < single_result.income_tax
    assert result.total_annual_tax < single_result.total_annual_tax


def test_estimate_unknown_tax_year_rejected():
    with pytest.raises(ValueError):
        estimate_quarterly_tax(Decimal("1000"), tax_year=2025)


def test_only_2026_supported():
    with pytest.raises(ValueError):
        bracket_table("single", tax_year=1999)


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def test_estimated_tax_threshold_constant():
    assert ESTIMATED_TAX_THRESHOLD == Decimal("1000.00")


def test_due_dates_present():
    from qtax.tax import QUARTERLY_DUE_DATES

    assert len(QUARTERLY_DUE_DATES) == 4
    assert "January 15" in QUARTERLY_DUE_DATES[-1]
