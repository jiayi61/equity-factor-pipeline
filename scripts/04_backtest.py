import os
import yaml
import numpy as np
import pandas as pd


def build_weights(dd: pd.DataFrame, factor_col: str, q: int) -> pd.Series:
    """
    Long top quantile, short bottom quantile, equal weight within each side.
    """
    dd = dd.dropna(subset=[factor_col]).copy()
    ranks = dd[factor_col].rank(method="first")
    bins = pd.qcut(ranks, q, labels=False)  # 0...(q-1)

    long_names = dd.loc[bins == (q - 1), "ticker"].tolist()
    short_names = dd.loc[bins == 0, "ticker"].tolist()

    w = pd.Series(0.0, index=dd["ticker"].values)
    if long_names:
        w.loc[long_names] = 1.0 / len(long_names)
    if short_names:
        w.loc[short_names] = -1.0 / len(short_names)
    return w


def turnover(prev_w: pd.Series, new_w: pd.Series) -> float:
    if prev_w is None:
        return float(new_w.abs().sum())
    idx = prev_w.index.union(new_w.index)
    p = prev_w.reindex(idx).fillna(0.0)
    n = new_w.reindex(idx).fillna(0.0)
    return float((n - p).abs().sum() / 2.0)


def step_backtest_5d(df: pd.DataFrame, factor_col: str, q: int, cost_bps_roundtrip: float) -> pd.DataFrame:
    """
    Step backtest aligned to 5-day horizon:
      - rebalance every 5 trading days
      - portfolio return = sum_i w_i * fwd_ret_5d(i,t) on rebalance date t
      - cost charged only on rebalance days

    Output rows are "rebalance dates" only (one row per 5 trading days).
    """
    out = []
    prev_w = None

    dates = sorted(df["date"].unique())
    # take every 5th date as rebalance date
    reb_dates = dates[::5]

    for dt in reb_dates:
        d = df[df["date"] == dt].copy()

        # require factor and fwd_ret_5d
        ok = d[factor_col].notna() & d["fwd_ret_5d"].notna()
        d = d.loc[ok, ["ticker", factor_col, "fwd_ret_5d"]].copy()
        if len(d) < max(q, 30):  # with 130 tickers this is fine
            continue

        w = build_weights(d[["ticker", factor_col]], factor_col=factor_col, q=q)
        y = d.set_index("ticker")["fwd_ret_5d"]

        gross_ret = float((w.reindex(y.index).fillna(0.0) * y).sum())

        tr = turnover(prev_w, w)
        cost = (cost_bps_roundtrip / 1e4) * tr
        net_ret = gross_ret - cost

        out.append((dt, gross_ret, cost, net_ret, tr))

        prev_w = w

    bt = pd.DataFrame(out, columns=["date", "gross_ret_5d", "cost", "net_ret_5d", "turnover"])
    bt = bt.sort_values("date")
    bt["equity"] = (1.0 + bt["net_ret_5d"]).cumprod()
    bt["drawdown"] = bt["equity"] / bt["equity"].cummax() - 1.0
    return bt


def perf_stats_step(bt: pd.DataFrame) -> dict:
    r = bt["net_ret_5d"].dropna()
    n = len(r)
    if n == 0:
        return {"n_steps": 0, "ann_ret": np.nan, "ann_vol": np.nan, "sharpe": np.nan, "max_dd": np.nan, "avg_turnover": np.nan}

    # one step ~ 5 trading days => about 252/5 steps per year
    steps_per_year = 252 / 5

    ann_ret = (1.0 + r.mean()) ** steps_per_year - 1.0
    ann_vol = r.std(ddof=1) * np.sqrt(steps_per_year)
    sharpe = ann_ret / ann_vol if ann_vol and not np.isnan(ann_vol) else np.nan
    max_dd = float(bt["drawdown"].min())
    avg_turn = float(bt["turnover"].mean())

    return {"n_steps": n, "ann_ret": float(ann_ret), "ann_vol": float(ann_vol), "sharpe": float(sharpe) if not np.isnan(sharpe) else np.nan, "max_dd": max_dd, "avg_turnover": avg_turn}


def main():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    q = int(cfg["research"]["quantiles"])                 # you set to 5
    cost_bps = float(cfg["research"]["cost_bps_roundtrip"])

    in_path = "data/processed/panel_factors.parquet"
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Missing {in_path}. Run scripts/02_preprocess.py first.")
    df = pd.read_parquet(in_path).sort_values(["date", "ticker"])

    factor = "rev_5"  # main factor

    bt = step_backtest_5d(df, factor_col=factor, q=q, cost_bps_roundtrip=cost_bps)
    if bt.empty:
        raise RuntimeError("Step backtest produced 0 rows. Check factor/label availability.")

    os.makedirs("results", exist_ok=True)
    out_path = f"results/backtest_{factor}_step5.csv"
    bt.to_csv(out_path, index=False)

    stats = perf_stats_step(bt)
    print(f"[OK] wrote {out_path}")
    print(
        f"STEP=5d | n_steps={stats['n_steps']} | ann_ret={stats['ann_ret']:.3%} | ann_vol={stats['ann_vol']:.3%} | "
        f"sharpe={stats['sharpe']:.2f} | max_dd={stats['max_dd']:.2%} | avg_turnover_per_reb={stats['avg_turnover']:.3f}"
    )


if __name__ == "__main__":
    main()
