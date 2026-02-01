# Equity Factor Research — Tech-Tilted US Universe (Yahoo Finance)

## Research setup
- **Universe:** 130 US equities (tech-tilted), daily data from Yahoo Finance (`yfinance`)
- **Sample period:** 1870 trading days (panel coverage after filters)
- **Prediction horizons (labels):** 1/5/10/20 trading days forward returns
- **Cross-sectional preprocessing:** winsorize (1%) + z-score per day
- **Quantile formation:** q = 5 (top vs bottom)
- **Transaction cost model:** constant round-trip 20 bps × turnover
- **Reproducibility:** `00_download → 01_build_panel → 02_preprocess → 03_evaluate → 04_backtest`

## Factor definition (main)
**rev_5** (short-term reversal):
\[
rev\_5(i,t) = -\left(\frac{P_{t}}{P_{t-5}} - 1\right)
\]
Intuition: recent winners tend to mean-revert over short horizons (especially in high-beta tech).

## Factor validation (IC / RankIC)
From `results/ic_summary.csv` (N≈130 per day, n_days=1870):
- **H=20:** RankIC_mean ≈ 0.0219, RankIC_IR ≈ 0.115, t ≈ 4.99  
- **H=10:** RankIC_IR ≈ 0.101, t ≈ 4.39  
- **H=5:**  RankIC_IR ≈ 0.124, t ≈ 5.36  

Interpretation: `rev_5` shows stable positive predictive power across multiple horizons.

## Backtest design (aligned to horizon)
To avoid horizon mismatch (IC on H-day forward returns vs daily PnL), we run a **5-day step backtest**:
- **Rebalance every 5 trading days**
- **Portfolio return uses `fwd_ret_5d`** on rebalance dates (aligned with validation target)
- Costs charged on rebalance dates only: bps × turnover

Backtest file: `results/backtest_rev_5_step5.csv`

### Backtest summary (cost-adjusted)
- **n_steps:** 374 (≈ 1870 / 5)
- **ann_ret:** 15.635%
- **ann_vol:** 25.874%
- **Sharpe:** 0.60
- **max_drawdown:** -29.36%
- **avg_turnover_per_rebalance:** 1.58

### Cost sensitivity (round-trip bps)

Using the same gross 5-day returns and realized turnover, we recompute net performance under different round-trip cost assumptions:

| Cost (bps, round-trip) | Ann. Return | Ann. Vol | Sharpe | MaxDD |
|---:|---:|---:|---:|---:|
| 0  | 35.50% | 25.87% | 1.37 | -17.84% |
| 10 | 25.18% | 25.87% | 0.97 | -20.10% |
| 20 | 15.63% | 25.87% | 0.60 | -29.36% |
| 50 | -8.93% | 25.89% | -0.34 | -68.96% |
| 100 | -38.98% | 25.93% | -1.50 | -97.96% |

Takeaway: performance degrades quickly as costs rise; the strategy is viable only under relatively low all-in costs (≈20 bps or below), motivating further turnover reduction and execution-aware modeling.


## Limitations
- Yahoo Finance data limitations (symbol mapping, survivorship/delistings depending on availability).
- Simplified transaction costs (constant bps); no explicit slippage/market impact modeling.
- No sector/size/beta neutralization yet.

## Next steps
1. Add risk controls: beta neutralization, sector neutrality, volatility targeting, position limits.
2. Cost sensitivity: test multiple bps levels + slippage proxy.
3. Walk-forward OOS: tune/lookback choices on train window, evaluate on holdout.
4. Extend factor library (fundamentals/news optional) and test interactions/ensembles.
