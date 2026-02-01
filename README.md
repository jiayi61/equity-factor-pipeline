# Equity Factor Research Pipeline (Demo)

A reproducible cross-sectional equity factor research pipeline:
data download -> panel alignment -> factor construction -> cross-sectional preprocessing ->
IC/RankIC & quantile tests -> cost-aware long/short backtest.

This repo is designed as a portfolio-quality demo: clear pipeline, explicit assumptions,
and reproducible outputs.

## What this repo does
- Builds a daily stock panel (OHLCV) from Yahoo Finance via yfinance
- Constructs interpretable baseline factors (momentum, reversal, volatility, liquidity proxy)
- Applies daily cross-sectional preprocessing (winsorize + z-score)
- Evaluates factors via IC / RankIC, decay across horizons, and quantile spread
- Runs a simple daily-rebalanced long/short top-bottom backtest with a constant bps cost model

## Repo structure
scripts/
  00_download.py        # download per-ticker data to data/raw/
  01_build_panel.py     # build aligned panel + forward-return labels
  02_preprocess.py      # compute factors + winsorize/zscore; saves panel_factors.parquet
  03_evaluate.py        # IC/RankIC, decay, quantile spread; writes results/*.csv
  04_backtest.py        # long-short backtest with costs; writes results/backtest_*.csv
data/
  tickers.csv           # local universe list
results/                # evaluation tables and backtest outputs (usually not committed)
report.md               # 1-page demo report

## Quickstart (macOS / zsh)
### 1) Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
pip install pyarrow
```

### 3) Prepare config + tickers
```bash
cp config.example.yaml config.yaml
# create data/tickers.csv (one column: ticker)
```

### 4) Run the pipeline
```bash
python scripts/00_download.py
python scripts/01_build_panel.py
python scripts/02_preprocess.py
python scripts/03_evaluate.py
python scripts/04_backtest.py
```

## Outputs
Processed data:
- data/processed/panel.parquet
- data/processed/panel_factors.parquet

Factor evaluation:
- results/ic_summary.csv
- results/decay_curve.csv
- results/quantile_spread.csv

Backtest:
- results/backtest_<factor>.csv

## Notes
- If you run with a toy universe (e.g., 10 tickers), statistics can be noisy.
- This repo prioritizes pipeline correctness and reproducibility over best performance.

## Report
See report.md for assumptions, evaluation outputs, and backtest results.

## License
MIT
<img width="468" height="637" alt="image" src="https://github.com/user-attachments/assets/4a11cbd9-ddbf-41c3-9e85-3d91d88bc799" />
