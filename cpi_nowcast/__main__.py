"""Command line entry point: python -m cpi_nowcast [--set "Component=forecast"]"""

import argparse
from pathlib import Path

from .backtest import load_prints, score, score_by_period
from .model import load_inputs, run

DEFAULT_WORKBOOK = Path(__file__).resolve().parent.parent / "workbook" / "CPI_Nowcast_Model_Sep2026.xlsx"


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute the September 2026 CPI nowcast from the workbook.")
    parser.add_argument("--workbook", default=DEFAULT_WORKBOOK, help="path to the nowcast workbook")
    parser.add_argument(
        "--set", action="append", default=[], metavar="COMPONENT=NSA_MOM",
        help="override one component's Sept NSA MoM forecast, e.g. --set \"Owners' equivalent rent=0.25\"",
    )
    args = parser.parse_args()

    inputs = load_inputs(args.workbook)
    by_name = {c.name.lower(): c for c in inputs.components}
    for override in args.set:
        name, _, value = override.rpartition("=")
        comp = by_name.get(name.strip().lower())
        if comp is None:
            parser.error(f"unknown component {name!r}; choose from: " + ", ".join(c.name for c in inputs.components))
        comp.forecast_nsa = float(value)

    r = run(inputs)
    print("September 2026 CPI nowcast")
    print(f"  Headline NSA MoM      {r.nsa_mom:6.3f}%")
    print(f"  Headline SA MoM       {r.sa_mom:6.3f}%")
    print(f"  YoY (unrounded)       {r.yoy:6.3f}%   ->  prints as {r.yoy_rounded:.1f}%")
    print(f"  Model SD of YoY       {r.sd_yoy:6.3f} pp")
    print(f"  P(lands in {r.yoy_rounded:.1f})      {r.p_rounded_bracket:6.1%}")
    print(f"  Core SA MoM           {r.core_sa_mom:6.3f}%")
    print(f"  Core YoY (unrounded)  {r.core_yoy:6.3f}%   ->  prints as {r.core_yoy_rounded:.1f}%")
    print()
    print("  P(YoY print above X)")
    for strike, p in r.p_above.items():
        print(f"    above {strike:.1f}%   {p:6.1%}")

    prints = load_prints(args.workbook)
    overall = score(prints)
    print()
    print(f"Backtest: {overall.n} prints, {prints[0].month} to {prints[-1].month}")
    print("  Period                  n   avg miss   YoY exact   YoY within 0.1")
    rows = list(score_by_period(prints).items()) + [("All prints", overall)]
    for name, s in rows:
        print(f"  {name:<22}{s.n:3d}   {s.mae_nsa:6.3f}     {s.yoy_exact:6.0%}      {s.yoy_within_one:6.0%}")


if __name__ == "__main__":
    main()
