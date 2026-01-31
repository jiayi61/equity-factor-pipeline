# Equity Factor Research Pipeline

Reproducible pipeline:
download -> panel alignment -> factor construction -> cross-sectional preprocessing
-> IC/RankIC + quantile spread -> long-short backtest with transaction costs.

## Quickstart

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
python scripts/00_download.py
python scripts/01_build_panel.py
python scripts/02_preprocess.py
python scripts/03_evaluate_factors.py
python scripts/04_backtest.py
