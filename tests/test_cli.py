"""Tests for the CLI (tests/test_cli.py)."""

from __future__ import annotations

import os

import pytest

from qtax.cli import main


def run(args, tmp_path):
    """Run main() with `--data-file` placed after the subcommand (argparse
    recognizes per-subcommand options that way)."""
    argv = list(args) + ["--data-file", str(tmp_path / "entries.json")]
    return main(argv)


def test_cli_add_income_and_list(tmp_path):
    assert run(["add-income", "1000.00", "--note", "book sale"], tmp_path) == 0
    assert run(["add-expense", "120.50", "--category", "software"], tmp_path) == 0


def test_cli_list_output_contains_entries(tmp_path, capsys):
    run(["add-income", "1000.00", "--note", "book sale", "--source", "KDP"], tmp_path)
    run(["list"], tmp_path)
    captured = capsys.readouterr()
    assert "book sale" in captured.out
    assert "KDP" in captured.out
    assert "1,000.00" in captured.out


def test_cli_estimate_output(tmp_path, capsys):
    code = run(["estimate", "100000", "--filing-status", "single"], tmp_path)
    assert code == 0
    captured = capsys.readouterr()
    assert "Quarterly estimated tax estimate" in captured.out
    assert "$25,745.30" in captured.out
    assert "$6,436.33" in captured.out


def test_cli_estimate_mfj(tmp_path, capsys):
    run(["estimate", "100000", "--filing-status", "married_filing_jointly"], tmp_path)
    captured = capsys.readouterr()
    assert "Married Filing Jointly" in captured.out


def test_cli_export_creates_csv(tmp_path):
    run(["add-income", "250.00", "--note", "royalty"], tmp_path)
    out = str(tmp_path / "out.csv")
    assert run(["export", out], tmp_path) == 0
    assert os.path.exists(out)


def test_cli_version(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "qtax" in captured.out


def test_cli_init(tmp_path):
    path = str(tmp_path / "fresh.json")
    assert main(["init", "--data-file", path]) == 0
    assert os.path.exists(path)