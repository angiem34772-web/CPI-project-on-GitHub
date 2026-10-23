# Backtest engine

[`backtest.py`](backtest.py) is the script that produced the 69-release backtest on the workbook's Backtest tab, including the trend-window, gasoline, and residual-category sensitivity tests and the naive benchmark.

It reads `panel_full.pkl`, a panel of first-published BLS CPI index levels, seasonally adjusted changes, relative-importance weights, seasonal factors, and EIA weekly gasoline prices, assembled release by release from the public sources listed in [`docs/METHODOLOGY.md`](../docs/METHODOLOGY.md). The panel itself is not included in this repository, so the script is here to document exactly how the backtest was run. The scored results it produced are in the workbook, and [`cpi_nowcast/backtest.py`](../cpi_nowcast/backtest.py) re-scores them.
