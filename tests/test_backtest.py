"""The Python backtest scoring must reproduce the Backtest tab's summary."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from cpi_nowcast.backtest import load_prints, score, score_by_period

WORKBOOK = Path(__file__).resolve().parent.parent / "workbook" / "CPI_Nowcast_Model_Sep2026.xlsx"


@pytest.fixture(scope="module")
def backtest_sheet():
    return load_workbook(WORKBOOK, data_only=True)["Backtest"]


@pytest.fixture(scope="module")
def prints():
    return load_prints(WORKBOOK)


def test_sample_size(prints):
    # Nov 2020 to Sep 2026, less Oct 2025, which BLS never published.
    assert len(prints) == 69
    assert prints[0].month == "2020-11"
    assert prints[-1].month == "2026-09"


@pytest.mark.parametrize("attr, cell", [
    ("mae_nsa", "B76"),
    ("rmse_nsa", "B77"),
    ("bias_nsa", "B78"),
    ("yoy_exact", "B79"),
    ("yoy_within_one", "B80"),
    ("sa_exact", "B81"),
    ("sa_miss_per_print", "B82"),
])
def test_summary_matches_spreadsheet(prints, backtest_sheet, attr, cell):
    assert getattr(score(prints), attr) == pytest.approx(backtest_sheet[cell].value, abs=1e-9)


def test_by_period_matches_spreadsheet(prints, backtest_sheet):
    periods = score_by_period(prints)
    for row in range(88, 93):
        name = backtest_sheet[f"A{row}"].value
        s = periods[name]
        assert s.n == backtest_sheet[f"B{row}"].value
        assert s.mae_nsa == pytest.approx(backtest_sheet[f"C{row}"].value, abs=1e-9)
        assert s.yoy_exact == pytest.approx(backtest_sheet[f"D{row}"].value, abs=1e-9)
        assert s.yoy_within_one == pytest.approx(backtest_sheet[f"E{row}"].value, abs=1e-9)


def test_beats_naive_forecast(prints):
    # Naive benchmark from the workbook: repeating last month's change misses by 0.273 on average.
    assert score(prints).mae_nsa < 0.273 / 2
