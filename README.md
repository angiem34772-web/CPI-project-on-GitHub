# CPI Nowcast Model

**An Excel and Python model that forecasts the monthly Consumer Price Index (CPI) from the bottom up, the same way the Bureau of Labor Statistics (BLS) builds it, and backtested on 69 monthly releases.**

Built by an Enrolled Agent and corporate tax analyst to show how a published government methodology can be turned into a transparent, auditable model, tested honestly against history, and checked independently in code.

> Built entirely from public data: BLS releases and seasonal factors, EIA gasoline prices, published forecaster previews, and Kalshi market prices. Not financial advice.

---

## In plain English

The CPI is the government's main inflation number. Each month the BLS measures price changes for hundreds of goods and services, weights each one by how much households spend on it, and adds them up.

Most forecasts start from the big picture. This model does the opposite: it makes a small, explainable forecast for each of 27 spending categories (rent, gasoline, used cars, airfare, and so on), then adds them up with the BLS weights. That gives:

1. **The headline and core forecast**, both seasonally adjusted (what Wall Street quotes) and unadjusted (what the official year-over-year number is based on).
2. **The exact number BLS would print**, rounded to one decimal, and how close the forecast sits to a rounding edge.
3. **A probability for every possible outcome**, so the forecast can be compared against prediction-market prices and other forecasters.
4. **A backtest** that replays the model on almost six years of past releases to measure how accurate it really is.

## The September 2026 forecast, scored

| | Model | Bloomberg consensus | Actual (Oct 14, 2026) |
|---|---:|---:|---:|
| Headline CPI, month over month (seasonally adjusted) | 0.6% | 0.6% | **0.6%** |
| Headline CPI, year over year | 3.7% | 3.6% | **3.7%** |
| Core CPI, month over month (seasonally adjusted) | 0.2% | 0.2% | **0.3%** |

The model called the headline exactly, including the year-over-year number that the consensus missed. It missed core by one notch, as did the consensus.

## How well does it work? The backtest

The model was replayed on **69 monthly CPI releases, from November 2020 through September 2026**. For each month it used only the data that was public before that release: the first-published numbers (not later revisions), the BLS weights available at the time, and that month's EIA gasoline prices. No judgment calls were added after the fact.

| Period | Releases | Average miss (points) | Exact year-over-year number | Within 0.1 |
|---|---:|---:|---:|---:|
| 2021 reopening | 14 | 0.23 | 0% | 38% |
| 2022 energy peak | 12 | 0.13 | 25% | 42% |
| 2023 disinflation | 12 | 0.05 | 67% | 100% |
| 2024 calm | 12 | 0.07 | 25% | 100% |
| 2025-26 tariffs and energy | 19 | 0.07 | 37% | 89% |
| **All releases** | **69** | **0.11** | **33%** | **78%** |

What the backtest shows:

- **It is 2.5 times more accurate than a naive forecast.** Assuming last month's change repeats misses by 0.27 points on average; the model misses by 0.11.
- **It has no lean.** The average error is close to zero, so it does not run consistently hot or cold.
- **Gasoline is the backbone.** Removing the EIA gasoline input doubles the average miss.
- **The economic backdrop matters more than any modeling choice.** In calm years the model is within one notch almost every month. In the 2021 reopening, when used cars, airfares, and hotels swung 5 to 10% a month, no trend-based model could keep up.

**Why the backtest starts in November 2020:**

- **COVID distortion.** From March to October 2020 the BLS suspended in-person price collection and filled many prices by estimate, so those months can't fairly test any model.
- **Seasonal factors.** The model uses the BLS 2026 seasonal factors, which were estimated on 2021 to 2025 data. Earlier months would be adjusted with factors that were never fitted to them.
- **Relevance.** Before 2020, inflation behaved differently: shelter rose about 0.3% every month, goods prices fell, and the headline rarely moved more than 0.2. Accuracy on 2015 to 2019 would say little about forecasting 2026.
- **Data.** The detailed category data used for the smaller categories was collected from December 2020 onward.

**How the months are weighted:** every month counts equally. With 69 months, down-weighting older ones would leave too few to tell modeling choices apart, and the goal was to see how the model behaves across very different economic periods. The by-period table above shows that more clearly than a single weighted average would. No model settings were fitted to the data, so there was nothing for recency weighting to tune.

**What the backtest changed.** An earlier 20-month backtest made the model look better than it is. Extending it to 69 months gave a more honest picture and showed that the model's stated confidence was too high: hitting the exact number one time in three implies a wider range of outcomes than the category-level math produces. The lesson is built into how the model's probabilities should be read.

Full details, including the sensitivity tests and known limitations, are in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

## Skills shown

| Area | What this project shows |
|---|---|
| Economic data | BLS CPI methodology: relative importance weights, weight roll-forward, seasonal adjustment, rounding |
| Excel modeling | Multi-tab workbook with a clear input / formula / output color convention, documented sources, and built-in checks |
| Testing and validation | An out-of-sample backtest across five economic periods, scored against a naive benchmark |
| Statistics | Combining category uncertainty into a forecast range and outcome probabilities |
| Python | An independent re-implementation that reproduces every spreadsheet result, with a command line for "what if" scenarios |
| Quality | 27 automated tests that fail if Python and the spreadsheet ever disagree |

## The workbook

[`workbook/CPI_Nowcast_Model_Sep2026.xlsx`](workbook/CPI_Nowcast_Model_Sep2026.xlsx)

| Tab | What it shows |
|---|---|
| README | How the model works and how to use it |
| Data | BLS CPI Table 1, exactly as published (August 2026 and September 2025 releases) |
| Nowcast | The 27 category forecasts, each with a standard error and a written rationale, adding up to headline and core |
| Opportunities | Every prediction-market contract where the model's probability differed from the market price |
| Backtest | The 69-release backtest, with summary statistics by period |
| Brackets | Model probability for each possible print, compared to market prices |
| Forecasters | Bank, consensus, and Federal Reserve forecasts converted to one comparable scale |
| Sources | Every data source, with links |
| Gasoline | EIA weekly gasoline prices converted to a CPI gasoline forecast |
| SeasonalFactors | The official BLS 2026 seasonal factors used to move between adjusted and unadjusted |

Blue cells are inputs, black cells are formulas, and yellow cells are key outputs.

## How to run the Python check

You need Python 3.10 or newer.

```bash
git clone https://github.com/angiem34772-web/CPI-project-on-GitHub.git
cd CPI-project-on-GitHub
pip install -r requirements.txt

python -m cpi_nowcast            # recomputes the forecast and scores the backtest
python -m pytest                 # confirms Python matches the spreadsheet
```

To test a scenario, override any category's forecast (unadjusted month-over-month %, as on the Nowcast tab):

```bash
python -m cpi_nowcast --set "Owners' equivalent rent=0.25"
```

That one change, a slightly softer shelter number, moves the forecast from 3.7% to 3.6%. The forecast sat only 0.006 points from a rounding edge, which shows how much rides on the largest category in the index.

## How the model works

For reviewers who want the detail ([`model.py`](cpi_nowcast/model.py) mirrors the Nowcast tab, and [`backtest.py`](cpi_nowcast/backtest.py) mirrors the Backtest tab's scoring):

1. **Weights.** BLS publishes each category's relative importance as of the prior month. The model rolls those forward one month by each category's price change relative to all items, which is how BLS does it before aggregating.
2. **Aggregation.** Headline change = the weighted sum of category forecasts, divided by the total rolled weight. Core uses only the goods and services categories.
3. **Year over year.** The official year-over-year figure is unadjusted, so the model forecasts unadjusted changes first: September 2026 index = August 2026 index × (1 + forecast), compared to the fixed September 2025 index. Seasonally adjusted figures are derived with the official BLS seasonal factors, for comparison with bank forecasts.
4. **Rounding.** BLS rounds to one decimal, half up. The model reports both the unrounded forecast and how far it is from the nearest rounding edge.
5. **Uncertainty.** Each category has a standard error. The total combines them with the BLS sampling error (0.04 points) and a model residual for what the categories miss. Outcome probabilities assume a normal distribution around the forecast.

## Assumptions and limits

- Category errors are treated as independent, and the backtest shows the resulting probabilities are somewhat too confident. Treat any single-bracket probability as an upper bound.
- The backtest uses the 2026 seasonal factors throughout, a small look-ahead for earlier years. BLS factors change little from year to year, so the effect is small.
- The model works at the level of 27 categories. It does not replicate the BLS item-level calculations inside each category.
- Gasoline is tied to EIA data. Used cars, airfare, and most services rely on recent trends plus judgment, each with its reasoning written next to it on the Nowcast tab.

## Project structure

```
workbook/        the Excel model
docs/            full methodology: data sources, backtest design, limitations
research/        the script that ran the 69-release backtest
cpi_nowcast/
  model.py       reads the workbook inputs and recomputes the forecast
  backtest.py    re-scores the backtest results saved in the workbook
  __main__.py    command line entry point
tests/           checks that Python reproduces every spreadsheet result
```

## About me

I'm an Enrolled Agent (EA) and corporate tax analyst specializing in complex partnerships. I'm interested in roles where financial expertise meets automation and data. See also my [Partnership Basis Tracker](https://github.com/angiem34772-web/partnership-basis-tracker).

Connect with me on [LinkedIn](https://www.linkedin.com/in/angie-jenkins-ea).

## License

MIT. See [LICENSE](LICENSE).
