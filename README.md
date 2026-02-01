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

<pre> 
equity-factor-pipeline/ 
├── Config/ 
│   ├── config.example.yaml # Config template (COMMIT) 
│   └── config.yaml # Local config (DO NOT COMMIT) 
├── Data/ 
│   ├── Raw/ # Per-ticker OHLCV downloads (DO NOT COMMIT) 
│   └── Processed/ # Aligned panels + factor tables (DO NOT COMMIT) 
├── Scripts/ # Deterministic pipeline entrypoints (00→04)
│   ├── 00_download.py # Download raw OHLCV into Data/Raw/ 
│   ├── 01_build_panel.py # Build aligned panel + forward-return labels 
│   ├── 02_preprocess.py # Build factors + winsorize/zscore; saves factor panel 
│   ├── 03_evaluate.py # IC/RankIC, decay, quantile spread; writes Outputs/Tables 
│   └── 04_backtest.py # Long-short backtest w/ costs; writes Outputs/Tables 
├── Outputs/ 
│   ├── Figures/ # Plots (IC time series, decay curve, equity curve)
│   └── Tables/ # CSV summaries (ic_summary, decay_curve, backtest_*.csv) 
├── Docs/ 
│   └── report.md # 1-page report: setup → results → limitations → next steps 
├── requirements.txt # Python deps (COMMIT)
├── .gitignore # Ignore Data/Raw, Data/Processed, local config, etc. (COMMIT)
└── README.md # Project overview + how to run + outputs 
</pre>


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
