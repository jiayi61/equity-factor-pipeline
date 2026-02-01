import os
import yaml
import numpy as np
import pandas as pd


# ---------------------------
# utils: winsorize + zscore
# ---------------------------
def winsorize(s: pd.Series, pct: float) -> pd.Series:
    if s.dropna().empty:
        return s
    lo = s.quantile(pct)
    hi = s.quantile(1 - pct)
    return s.clip(lo, hi)


def zscore(s: pd.Series) -> pd.Series:
    m = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return s * np.nan
    return (s - m) / sd


def preprocess_cross_section(df: pd.DataFrame, factor_cols, winsor_pct: float) -> pd.DataFrame:
    out = []
    for date, d in df.groupby("date"):
        dd = d.copy()
        for col in factor_cols:
            x = dd[col]
            x = winsorize(x, winsor_pct)
            x = zscore(x)
            dd[col] = x
        out.append(dd)
    return pd.concat(out, ignore_index=True)


# ---------------------------
# factor construction
# ---------------------------
def compute_factors(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Expects columns from 01 (snake_case):
      date, ticker, open, high, low, close, adj_close, volume, ret_1d, fwd_ret_*d
    """
    df = panel.sort_values(["ticker", "date"]).copy()
    g = df.groupby("ticker", group_keys=False)

    # Momentum / reversal
    df["mom_20"] = g["adj_close"].pct_change(20)
    df["mom_60"] = g["adj_close"].pct_change(60)
    df["rev_5"]  = -g["adj_close"].pct_change(5)

    # Volatility: rolling std of daily returns
    df["vol_20"] = (
        g["ret_1d"]
        .rolling(20, min_periods=20)
        .std()
        .reset_index(level=0, drop=True)
    )

    # Amihud: rolling mean(|ret| / dollar_volume)
    # dollar_volume = close * volume
    dollar_vol = (df["close"] * df["volume"]).replace(0, np.nan)
    amihud_daily = df["ret_1d"].abs() / dollar_vol
    df["amihud_20"] = (
        amihud_daily.groupby(df["ticker"])
        .rolling(20, min_periods=20)
        .mean()
        .reset_index(level=0, drop=True)
    )

    # Volume surprise: volume / rolling_mean(volume,20) - 1
    vol_mean_20 = (
        g["volume"]
        .rolling(20, min_periods=20)
        .mean()
        .reset_index(level=0, drop=True)
    )
    df["volu_z_20"] = df["volume"] / vol_mean_20 - 1.0

    return df


def main():
    # 0) load config
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    winsor_pct = cfg["research"]["winsor_pct"]
    min_hist = cfg["research"]["min_history_days"]
    horizons = cfg["research"]["horizons"]

    in_path = "data/processed/panel.parquet"
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Missing {in_path}. Run scripts/01_build_panel.py first.")

    panel = pd.read_parquet(in_path)

    # 1) compute factors
    panel = compute_factors(panel)

    factor_cols = ["mom_20", "mom_60", "rev_5", "vol_20", "amihud_20", "volu_z_20"]

    # 2) filter: enough history per ticker
    panel = panel.sort_values(["ticker", "date"]).copy()
    panel["hist_ok"] = panel.groupby("ticker").cumcount() >= min_hist

    # 3) filter: require forward returns labels exist (so evaluation later is valid)
    # keep only rows where ALL horizons exist (strict but clean)
    for h in horizons:
        panel = panel[panel[f"fwd_ret_{h}d"].notna()]
    panel = panel[panel["hist_ok"]].drop(columns=["hist_ok"])

    # 4) cross-sectional preprocess (winsorize + zscore each date)
    panel = preprocess_cross_section(panel, factor_cols=factor_cols, winsor_pct=winsor_pct)

    # 5) save
    os.makedirs("data/processed", exist_ok=True)
    out_path = "data/processed/panel_factors.parquet"
    panel.to_parquet(out_path, index=False)

    print(f"[OK] saved: {out_path} | rows={len(panel):,} | tickers={panel['ticker'].nunique()} | dates={panel['date'].nunique()}")


if __name__ == "__main__":
    main()
