"""The Python model must reproduce the workbook's own spreadsheet results."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from cpi_nowcast.model import load_inputs, round_half_up, run

WORKBOOK = Path(__file__).resolve().parent.parent / "workbook" / "CPI_Nowcast_Model_Sep2026.xlsx"


@pytest.fixture(scope="module")
def sheets():
    """Values the spreadsheet calculated and saved in the workbook."""
    wb = load_workbook(WORKBOOK, data_only=True)
    return wb["Nowcast"], wb["Brackets"]


@pytest.fixture
def result():
    return run(load_inputs(WORKBOOK))


@pytest.mark.parametrize("attr, cell", [
    ("nsa_mom", "B43"),
    ("sa_mom", "B44"),
    ("index_sep", "B45"),
    ("yoy", "B46"),
    ("yoy_rounded", "B47"),
    ("sd_mom", "B50"),
    ("sd_yoy", "B51"),
    ("p_rounded_bracket", "B52"),
    ("core_nsa_mom", "B56"),
    ("core_sa_mom", "B57"),
    ("core_yoy", "B59"),
    ("core_yoy_rounded", "B60"),
])
def test_matches_spreadsheet_nowcast(result, sheets, attr, cell):
    nowcast, _ = sheets
    assert getattr(result, attr) == pytest.approx(nowcast[cell].value, abs=1e-9)


def test_matches_spreadsheet_bracket_probabilities(result, sheets):
    _, brackets = sheets
    for row in range(11, 18):
        strike = brackets[f"B{row}"].value
        assert result.p_above[strike] == pytest.approx(brackets[f"E{row}"].value, abs=1e-9)


def test_rolled_weights_match_spreadsheet(sheets):
    nowcast, _ = sheets
    inputs = load_inputs(WORKBOOK)
    run(inputs)
    for offset, comp in enumerate(inputs.components):
        assert comp.weight == pytest.approx(nowcast[f"E{13 + offset}"].value, abs=1e-9)


def test_jul_weights_sum_to_100():
    inputs = load_inputs(WORKBOOK)
    assert sum(c.weight_jul for c in inputs.components) == pytest.approx(100, abs=1e-6)


def test_higher_shelter_forecast_raises_headline():
    inputs = load_inputs(WORKBOOK)
    base = run(inputs).yoy
    oer = next(c for c in inputs.components if c.name == "Owners' equivalent rent")
    oer.forecast_nsa += 0.1
    # OER is about 26% of the index, so +0.1pp on OER is about +0.026pp on headline MoM.
    assert run(inputs).yoy - base == pytest.approx(0.026, abs=0.002)


def test_round_half_up_matches_excel():
    assert round_half_up(3.65) == 3.7
    assert round_half_up(3.6499) == 3.6
    assert round_half_up(-0.25) == -0.3
