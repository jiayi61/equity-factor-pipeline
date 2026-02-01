import os
import yaml
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def daily_ic(df: pd.DataFrame, factor_col: str, y_col: str, rank: bool, min_n: int) -> pd.DataFrame:
    out = []
    for date, d in df.groupby("date"):
        x = d[factor_col]
        y = d[y_col]
        ok = x.notna() & y.notna()
        if ok.sum() < min_n:
            continue
        if rank:
            ic = spearmanr(x[ok].values, y[ok].values).correlation
        else:
            ic = np.corrcoef(x[ok].values, y[ok].values)[0, 1]
        out.append((date, ic))
    return pd.DataFrame(out, columns=["date", "ic"]).sort_values("date")


def ic_summary(ic_df: pd.DataFrame) -> dict:
    if ic_df.empty:
        return {"mean": np.nan, "std": np.nan, "icir": np.nan, "tstat": np.nan, "n_days": 0}
    m = ic_df["ic"].mean()
    s = ic_df["ic"].std(ddof=1)
    n = ic_df["ic"].count()
    icir = m / s if s and not np.isnan(s) else np.nan
    tstat = m / (s / np.sqrt(n)) if s and n > 1 and not np.isnan(s) else np.nan
    return {"mean": m, "std": s, "icir": icir, "tstat": tstat, "n_days": n}


def quantile_spread(df: pd.DataFrame, factor_col: str, y_col: str, q: int, min_n: int) -> pd.DataFrame:
    rows = []
    for date, d in df.groupby("date"):
        x = d[factor_col]
        y = d[y_col]
        ok = x.notna() & y.notna()
        if ok.sum() < min_n:
            continue

        dd = pd.DataFrame({"x": x[ok].values, "y": y[ok].values})
        ranks = dd["x"].rank(method="first")

        # qcut needs at least q samples
        bins = pd.qcut(ranks, q, labels=False)

        mean_by_bin = dd.groupby(bins)["y"].mean()
        spread = float(mean_by_bin.iloc[-1] - mean_by_bin.iloc[0])
        rows.append((date, spread))

    return pd.DataFrame(rows, columns=["date", "top_minus_bottom"]).sort_values("date")


def main():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    horizons = cfg["research"]["horizons"]
    q = int(cfg["research"]["quantiles"])

    in_path = "data/processed/panel_factors.parquet"
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Missing {in_path}. Run scripts/02_preprocess.py first.")
    df = pd.read_parquet(in_path)

    # ---- KEY FIX: adapt thresholds to your universe size ----
    # For IC: need enough cross-sectional names; with 10 tickers, set ~8-10.
    min_n_ic = max(8, min(30, df["ticker"].nunique()))
    # For quantile spread: must have >= q, plus a little slack
    min_n_spread = max(q, min_n_ic)

    factors = ["mom_20", "mom_60", "rev_5", "vol_20", "amihud_20", "volu_z_20"]

    os.makedirs("results", exist_ok=True)

    summary_rows = []
    decay_rows = []
    spread_rows = []

    for fac in factors:
        for h in horizons:
            ycol = f"fwd_ret_{h}d"

            ic_df = daily_ic(df, fac, ycol, rank=False, min_n=min_n_ic)
            ric_df = daily_ic(df, fac, ycol, rank=True, min_n=min_n_ic)

            s_ic = ic_summary(ic_df)
            s_ric = ic_summary(ric_df)

            summary_rows.append({
                "factor": fac, "h": h,
                "IC_mean": s_ic["mean"], "IC_std": s_ic["std"], "IC_IR": s_ic["icir"], "IC_t": s_ic["tstat"],
                "RankIC_mean": s_ric["mean"], "RankIC_std": s_ric["std"], "RankIC_IR": s_ric["icir"], "RankIC_t": s_ric["tstat"],
                "n_days": s_ic["n_days"],
            })

            decay_rows.append({
                "factor": fac, "h": h,
                "RankIC_mean": s_ric["mean"],
                "RankIC_IR": s_ric["icir"],
                "RankIC_t": s_ric["tstat"],
                "n_days": s_ric["n_days"],
            })

            sp = quantile_spread(df, fac, ycol, q=q, min_n=min_n_spread)
            sp["factor"] = fac
            sp["h"] = h
            spread_rows.append(sp)

    pd.DataFrame(summary_rows).sort_values(["factor", "h"]).to_csv("results/ic_summary.csv", index=False)
    pd.DataFrame(decay_rows).sort_values(["factor", "h"]).to_csv("results/decay_curve.csv", index=False)
    pd.concat(spread_rows, ignore_index=True).to_csv("results/quantile_spread.csv", index=False)

    print("[OK] wrote results/ic_summary.csv, results/decay_curve.csv, results/quantile_spread.csv")
    print(f"[INFO] thresholds: min_n_ic={min_n_ic}, min_n_spread={min_n_spread}, tickers={df['ticker'].nunique()}")


if __name__ == "__main__":
    main()

