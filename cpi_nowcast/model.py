"""Bottom-up CPI nowcast: the same math as the workbook's Nowcast tab.

The workbook is the source of truth for inputs. This module reads each
component's BLS weight, last month's price change, and the forecast inputs
(blue cells on the Nowcast tab), then recomputes the weight roll-forward,
aggregation, rounding, and probabilities independently of Excel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook

NOWCAST_FIRST_ROW = 13
NOWCAST_END_LABEL = "Check: weights sum"
BRACKET_STRIKES = (3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9)


@dataclass
class Component:
    name: str
    group: str            # F food, E energy, G core goods, S core services
    weight_jul: float     # BLS relative importance, Jul 2026
    aug_change: float     # Jul->Aug NSA price change (decimal)
    forecast_nsa: float   # Sept NSA MoM forecast (%)
    se: float             # forecast standard error (pp)
    sa_gap: float         # Sept SA minus NSA gap (pp)
    weight: float = 0.0   # relative importance rolled forward to Aug 2026

    @property
    def forecast_sa(self) -> float:
        return self.forecast_nsa + self.sa_gap


@dataclass
class Inputs:
    index_aug: float          # all items, Aug 2026 (NSA)
    index_base: float         # all items, Sep 2025 (the YoY base)
    core_aug: float
    core_base: float
    all_items_aug_change: float
    sampling_se: float
    residual_se: float
    components: list[Component] = field(default_factory=list)


@dataclass
class Result:
    nsa_mom: float
    sa_mom: float
    index_sep: float
    yoy: float
    yoy_rounded: float
    sd_mom: float
    sd_yoy: float
    p_rounded_bracket: float
    core_nsa_mom: float
    core_sa_mom: float
    core_yoy: float
    core_yoy_rounded: float
    p_above: dict[float, float]


def round_half_up(x: float, places: int = 1) -> float:
    """Excel ROUND (half away from zero), which BLS rounding also follows."""
    q = 10 ** places
    return math.floor(abs(x) * q + 0.5 + 1e-9) / q * (1 if x >= 0 else -1)


def normal_cdf(x: float, mean: float, sd: float) -> float:
    return 0.5 * (1 + math.erf((x - mean) / (sd * math.sqrt(2))))


def load_inputs(path: str | Path) -> Inputs:
    nowcast = load_workbook(path, data_only=True)["Nowcast"]

    def num(cell: str) -> float:
        return float(nowcast[cell].value)

    inputs = Inputs(
        index_aug=num("B4"),
        index_base=num("B5"),
        core_aug=num("B6"),
        core_base=num("B7"),
        all_items_aug_change=num("B8"),
        sampling_se=num("B9"),
        residual_se=num("B10"),
    )

    row = NOWCAST_FIRST_ROW
    while not str(nowcast[f"A{row}"].value).startswith(NOWCAST_END_LABEL):
        inputs.components.append(Component(
            name=nowcast[f"A{row}"].value,
            group=nowcast[f"M{row}"].value,
            weight_jul=num(f"B{row}"),
            aug_change=num(f"C{row}"),
            forecast_nsa=num(f"F{row}"),
            se=num(f"G{row}"),
            sa_gap=num(f"H{row}"),
        ))
        row += 1
    return inputs


def run(inputs: Inputs) -> Result:
    comps = inputs.components

    # BLS publishes relative importances for the prior month; roll them forward
    # by each category's price change relative to all items.
    for c in comps:
        c.weight = c.weight_jul * (1 + c.aug_change) / (1 + inputs.all_items_aug_change)

    def aggregate(subset: list[Component]) -> tuple[float, float]:
        w = sum(c.weight for c in subset)
        nsa = sum(c.weight * c.forecast_nsa for c in subset) / w
        sa = sum(c.weight * c.forecast_sa for c in subset) / w
        return nsa, sa

    nsa_mom, sa_mom = aggregate(comps)
    index_sep = inputs.index_aug * (1 + nsa_mom / 100)
    yoy = (index_sep / inputs.index_base - 1) * 100
    yoy_rounded = round_half_up(yoy)

    # Component errors treated as independent, plus BLS sampling error and a
    # residual for what the components miss.
    component_var = sum((c.weight * c.se / 100) ** 2 for c in comps)
    sd_mom = math.sqrt(component_var + inputs.sampling_se ** 2 + inputs.residual_se ** 2)
    sd_yoy = sd_mom * inputs.index_aug / inputs.index_base

    p_rounded = (normal_cdf(yoy_rounded + 0.05, yoy, sd_yoy)
                 - normal_cdf(yoy_rounded - 0.05, yoy, sd_yoy))

    # "Above X" settles YES on a one-decimal print of X + 0.1 or more,
    # i.e. an unrounded YoY of at least X + 0.05.
    p_above = {x: 1 - normal_cdf(x + 0.05, yoy, sd_yoy) for x in BRACKET_STRIKES}

    core = [c for c in comps if c.group in ("G", "S")]
    core_nsa, core_sa = aggregate(core)
    core_yoy = (inputs.core_aug * (1 + core_nsa / 100) / inputs.core_base - 1) * 100

    return Result(
        nsa_mom=nsa_mom,
        sa_mom=sa_mom,
        index_sep=index_sep,
        yoy=yoy,
        yoy_rounded=yoy_rounded,
        sd_mom=sd_mom,
        sd_yoy=sd_yoy,
        p_rounded_bracket=p_rounded,
        core_nsa_mom=core_nsa,
        core_sa_mom=core_sa,
        core_yoy=core_yoy,
        core_yoy_rounded=round_half_up(core_yoy),
        p_above=p_above,
    )
