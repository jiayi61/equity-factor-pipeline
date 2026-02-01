import os
import glob
import yaml
import pandas as pd
from tqdm import tqdm


def _flatten_and_dedup(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    # Handle MultiIndex columns (yfinance can produce these)
    if isinstance(df.columns, pd.MultiIndex):
        last = df.columns.get_level_values(-1)
        if ticker in set(last):
            df = df.xs(ticker, axis=1, level=-1)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns.to_list()]

    # Flatten tuple colnames
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    # Drop duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()].copy()

    return df


def _norm(c: str) -> str:
    return str(c).strip().replace(" ", "_").replace("-", "_").lower()


def main():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    price_field_cfg = cfg["data"]["price_field"]  # "Adj Close" recommended
    horizons = cfg["research"]["horizons"]

    files = sorted(glob.glob("data/raw/*.parquet"))
    if len(files) == 0:
        raise FileNotFoundError("No raw parquet files found in data/raw/. Run scripts/00_download.py first.")

    rows = []
    for fp in tqdm(files, desc="Reading raw files"):
        ticker = os.path.basename(fp).replace(".parquet", "")

        df = pd.read_parquet(fp)
        df = _flatten_and_dedup(df, ticker=ticker)

        # ---- ensure date is a column ----
        # If date is stored in index, move it to a column
        if "date" not in df.columns and "Date" not in df.columns:
            try:
                dt = pd.to_datetime(df.index)
                df = df.copy()
                df["date"] = dt
            except Exception:
                pass

        # If still no date, try common fallback names
        if "date" not in df.columns:
            if "Date" in df.columns:
                df = df.rename(columns={"Date": "date"})
            elif "index" in df.columns:
                df = df.rename(columns={"index": "date"})
            else:
                raise KeyError(f"'date' not found for {ticker}. cols={list(df.columns)}")

        # normalize colnames to snake_case
        df = df.rename(columns={c: _norm(c) for c in df.columns})
        df["ticker"] = ticker

        # Keep standard fields
        keep = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
        for c in keep:
            if c not in df.columns:
                df[c] = pd.NA
        df = df[keep]

        rows.append(df.reset_index(drop=True))

    panel = pd.concat(rows, ignore_index=True)
    panel["date"] = pd.to_datetime(panel["date"])
    panel = panel.sort_values(["ticker", "date"]).reset_index(drop=True)

    # map config price_field to normalized column name
    pf = _norm(price_field_cfg)  # "Adj Close" -> "adj_close"
    if pf not in panel.columns:
        # fallback
        pf = "close"

    panel[pf] = pd.to_numeric(panel[pf], errors="coerce")

    panel["ret_1d"] = panel.groupby("ticker")[pf].pct_change()

    for h in horizons:
        fwd_px = panel.groupby("ticker")[pf].shift(-h)
        panel[f"fwd_ret_{h}d"] = fwd_px / panel[pf] - 1.0

    os.makedirs("data/processed", exist_ok=True)
    out_path = "data/processed/panel.parquet"
    panel.to_parquet(out_path, index=False)

    print(f"[OK] saved panel: {out_path} | rows={len(panel):,} | tickers={panel['ticker'].nunique()}")


if __name__ == "__main__":
    main()
