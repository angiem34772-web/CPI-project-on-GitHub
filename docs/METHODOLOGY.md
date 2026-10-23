# CPI Nowcast Model — Methodology

A bottom-up, component-level model of the U.S. Consumer Price Index built to price
Kalshi's inflation contracts. It replicates the BLS aggregation structure (weighted
component changes → unrounded headline/core → rounded one-decimal YoY) rather than
forecasting the headline directly.

Inspired by the approach described in Bloomberg's October 13, 2026 profile of Kalshi
trader Brian Golden: a spreadsheet that mimics BLS methodology, "a bunch of good small
guesses" rather than a macro view.

---

## 1. What the model does

For a target month *t*:

1. **Component forecast.** For each of 23 expenditure categories, forecast the
   not-seasonally-adjusted (NSA) month-over-month change as
   `trailing mean of the last k published SA changes − seasonal gap(t)`.
   - Gasoline is the exception: its NSA change is taken directly from the EIA weekly
     retail price series (monthly average of week-ending prices).
   - The seasonal gap is `(factor[t−1] / factor[t] − 1) × 100` from the official BLS
     seasonal-factor file. Categories without a published factor (apparel, lodging,
     the Table 3 aggregates) use a weighted average of their sub-series' factors.
2. **Aggregation.** Weighted sum using BLS relative-importance weights, rolled
   forward by each component's price relative as the BLS does. ~95% of the basket
   is modeled explicitly; the ~5% remainder uses the core trend.
3. **Outputs.** Unrounded headline NSA MoM → implied index level → unrounded YoY
   (against the published base-month index) → rounded YoY (what Kalshi settles on).
   SA MoM is derived for comparison with bank forecasts. Core is aggregated separately.
4. **Uncertainty.** `SD = sqrt(Σ(w_i × se_i)² + BLS sampling SE² + model residual²)`,
   where `se_i` is the 12-month standard deviation of each component's SA change.
   Bracket probabilities are normal-distribution integrals over the rounding window.

The model is in Excel ([`workbook/CPI_Nowcast_Model_Sep2026.xlsx`](../workbook/CPI_Nowcast_Model_Sep2026.xlsx));
every number flows from blue input cells through formulas. The backtest engine is
[`research/backtest.py`](../research/backtest.py).

## 2. Data sources

| Input | Source | Notes |
|---|---|---|
| Component index levels, SA/NSA changes, weights | BLS CPI news releases, Table 1 and Table 3, archived at bls.gov/bls/news-release/cpi.htm | Pulled release by release; values exactly as first published |
| Seasonal factors | bls.gov/web/cpi/cpi-seasonal-factors.xlsx (2026 file, calculated through Dec 2025) | Updated by BLS each February |
| Gasoline | EIA weekly U.S. regular all-formulations retail price (series EMM_EPMR_PTE_NUS_DPG) | Monthly average of week-ending prices |
| Used cars (judgment input) | Manheim Used Vehicle Value Index (Cox Automotive), mid-month and full-month | Leads CPI used cars by ~2 months |
| Market prices | Kalshi public API, `api.elections.kalshi.com/trade-api/v2` | Snapshot at time of analysis |

## 3. Backtest

### Window and why

**November 2020 – September 2026, 69 monthly prints.** October 2025 is excluded
because the BLS did not publish it (lapse in appropriations).

Why not earlier:

- **Seasonal factors.** The model uses the BLS 2026 factor file, estimated on
  2021–2025 data. Testing on months before 2021 would apply seasonal adjustment the
  factors were never fitted to.
- **Regime relevance.** Pre-2020 CPI behaved differently in ways that matter for the
  model structure: shelter ran ~0.3 every month, core goods deflated, gasoline's weight
  was smaller, headline rarely moved more than 0.2. Performance on 2015–2019 would say
  little about trading 2026.
- **COVID distortion.** March–October 2020 saw suspended in-person collection and
  heavy imputation by the BLS; those months are not usable as a test of any model.
- **Data availability.** The Table 3 aggregates (household furnishings, recreation,
  education, communication, other goods) that the model uses for the residual
  categories were pulled from December 2020 onward, which is the binding constraint.

### Out-of-sample discipline

Each month's forecast uses only information available before that release:

- Index levels and SA changes from releases published before the target month.
- **First-published** SA values for the trend inputs, not later revisions (BLS revises
  five years of seasonally adjusted data each February).
- Relative-importance weights carried forward from the most recent published release,
  as the BLS itself does between annual updates.
- EIA gasoline for the target month only (which is available by the end of that month,
  before the CPI release).

No parameter was fit to the test set. The one choice informed by the backtest was the
trend window, and the backtest showed it does not matter (see below).

### Weighting

**None.** All 69 months count equally. Reasons:

- With 69 observations, down-weighting half of them leaves too few to distinguish
  modeling choices.
- The purpose was to see how the model behaves *across* regimes. The by-period
  breakdown (below) carries that information better than a weighted average would.
- No parameters were estimated, so there was nothing for recency weighting to tune.

### Results

| Metric | Full sample (n=69) |
|---|---|
| Mean absolute error, NSA MoM | 0.111 pp |
| RMSE | 0.160 pp |
| Bias | −0.004 pp |
| YoY rounded bracket, exact hit | 33% |
| YoY within one bracket (±0.1) | 78% |
| SA MoM rounded, exact hit | 35% |
| Mean \|SA error\| per print (Bloomberg's criterion) | 0.107 |
| Naive benchmark (last month's NSA repeats) | MAE 0.273 |

By period:

| Period | n | MAE | YoY exact | YoY ±0.1 |
|---|---|---|---|---|
| Nov 2020 – Dec 2021 (reopening) | 14 | 0.230 | 0% | 38% |
| 2022 (energy peak) | 12 | 0.127 | 25% | 42% |
| 2023 (disinflation) | 12 | 0.052 | 67% | 100% |
| 2024 (calm) | 12 | 0.072 | 25% | 100% |
| Jan 2025 – Sep 2026 (tariff / energy) | 19 | 0.074 | 37% | 89% |

Sensitivity:

| Variant | MAE |
|---|---|
| Trend window 2 / 3 / 4 / 6 months | 0.103 / 0.107 / 0.111 / 0.111 |
| Trend window 12 months | 0.123 |
| Without EIA gasoline | 0.213 |
| Without residual-category modeling | 0.121 |

### What the backtest shows

1. **Gasoline via EIA is the backbone.** Removing it doubles the error in every
   regime. Everything else combined is worth less than this one weekly series.
2. **Regime matters more than any modeling choice.** In a calm disinflation year the
   model hits the exact bracket two-thirds of the time; in a reopening shock it never
   does. Used cars, airfares, and lodging swinging 5–10% a month are not forecastable
   from trends.
3. **The trend window is a wash.** 2–6 months are within 0.01 of each other. A
   20-print pilot backtest had suggested 4 was best; that was noise.
4. **The model is a floor, not an edge.** It is ~2.5× better than naive and roughly
   equal to a mid-tier bank desk on Bloomberg's cumulative-error criterion. Beating
   the best forecasters requires a judgment layer on top (Manheim, airfares, insurance
   filings, collection-timing quirks).

### What the backtest does not show

- **Probability calibration.** The backtest validates the point estimate, not the
  per-bet probabilities. The 33% exact-hit rate implies an effective YoY SD of ~0.13,
  wider than the ~0.10 the component variance produces. Bracket probabilities from the
  component math are therefore somewhat overconfident, and model-specification
  uncertainty (e.g. the two trend windows disagreeing by 0.05 on a given month) is not
  in them at all. **Rule adopted:** a model-vs-market difference counts only if it
  survives both the 3- and 4-month windows.
- **Forward performance.** 69 months is enough to rule out bad ideas, not enough to
  prove a persistent edge. Scoring each new release as it is published is the real test.

## 4. Known limitations

- 2026 seasonal factors applied to 2021–2024 rows (mild look-ahead; BLS factors move
  little year to year, but not zero).
- EIA monthly average is a proxy for the BLS gasoline sample; residual SD vs actual
  CPI gasoline is ~0.5 pp over 22 months, no bias.
- Residual-category seasonal gaps use proxy weightings of published sub-series.
- The model structure was designed in October 2026 with knowledge of how 2025–26
  unfolded; the parameters are not fitted, but the choice of which components to
  break out is informed by hindsight.
- Component errors are treated as independent. The September 2026 miss (−0.08,
  several core components hot at once) suggests they are positively correlated, which
  argues for the wider effective SD above.
- Tobacco was rebased by BLS to Dec 2024 = 100; historical levels are rescaled by the
  Dec 2024 ratio so changes chain correctly.
- Hospital services index is blank in several published tables (Oct 2022, Aug 2024);
  those cells are left empty, not imputed.

## 5. Live record

| Date | Print | Model | Actual | Result |
|---|---|---|---|---|
| 2026-10-14 | Sep 2026 YoY | 3.656 (bracket 3.7) | 3.738 (bracket 3.7) | Hit; 0.08 cool on NSA |

## 6. Update cadence

- **Monthly, release morning:** new Table 1/3 into the Data panel, actuals into the
  Backtest tab, gasoline residual into the Gasoline tab.
- **Weekly, Monday:** EIA gasoline price.
- **Week before release:** Manheim, airfare indices, bank previews; set judgment cells;
  compare bracket probabilities to Kalshi prices (Opportunities tab).
- **Annually, February:** new BLS seasonal-factor file.

---

*Not financial advice. Built October 2026.*
