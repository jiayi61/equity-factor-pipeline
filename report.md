# Equity Factor Research — Demo Report (Yahoo Finance)

## Research setup
- **Universe:** 10 US large-cap tickers (toy universe for pipeline validation)
- **Data:** daily OHLCV from Yahoo Finance (`yfinance`)
- **Sample period:** ~1870 trading days (see `data/processed/panel.parquet`)
- **Prediction horizons (labels):** 1/5/10/20 trading days forward returns
- **Cross-sectional preprocessing:** winsorize (1%) + z-score per day
- **Portfolio formation:** daily rebalanced long–short **top vs bottom quantile** (q = <Q>)
- **Transaction cost model:** constant **round-trip <COST_BPS> bps** (see `config.yaml`)
- **Reproducibility:** run `scripts/00_download.py → 01_build_panel.py → 02_preprocess.py → 03_evaluate.py → 04_backtest.py`

## Factor definition (example)
**vol_20**: 20-day rolling volatility of daily returns  
\[
vol_{20}(i,t) = \mathrm{Std}(\mathrm{ret}_{1d}(i,t-19:t))
\]

## Factor validation
Outputs saved in:
- `results/ic_summary.csv` — IC / RankIC mean, IR, t-stat by horizon
- `results/decay_curve.csv` — RankIC vs horizon (decay)
- `results/quantile_spread.csv` — top-minus-bottom forward return spread

Notes:
- With a **toy universe (N=10)**, IC estimates are noisy and mainly used to validate the end-to-end pipeline.
- Next step is to expand universe to 100–300 liquid tickers to obtain stable cross-sectional statistics.

## Backtest (long–short top/bottom, cost-adjusted)
Backtest file: `results/backtest_vol_20.csv`

Summary (cost-adjusted):
- **n_days:** 1870
- **ann_ret:** 8.156%
- **ann_vol:** 67.432%
- **Sharpe:** 0.12
- **max_drawdown:** -91.22%
- **avg_turnover:** 0.192

Interpretation:
- The factor is **not profitable** under this simple long–short formulation on the toy universe.
- The large drawdown is consistent with **small-universe concentration + simplistic long/short construction**; this is treated as a diagnostic outcome, not a production result.

## Limitations
- **Small universe (N=10)** → unstable IC/quantile tests and concentrated portfolios.
- Yahoo Finance data limitations (e.g., delistings/survivorship).
- Simplified transaction costs (constant bps) and no slippage/market impact.

## Next steps (to make this “real”)
1. Expand tickers to 100–300 (or use a standard index universe).
2. Set `quantiles=5` and re-run evaluation/backtest.
3. Add walk-forward OOS: tune parameters on train window, evaluate on holdout.
4. Add risk controls / neutralization (market beta, sector, size).
