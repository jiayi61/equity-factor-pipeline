import os
import yaml
import pandas as pd
import yfinance as yf
from tqdm import tqdm

def main():
    # read config
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    tickers = pd.read_csv(cfg["universe"]["tickers_csv"])["ticker"].dropna().unique().tolist()
    start, end = cfg["data"]["start"], cfg["data"]["end"]

    os.makedirs("data/raw", exist_ok=True)

    for tkr in tqdm(tickers, desc="Downloading"):
        df = yf.download(tkr, start=start, end=end, auto_adjust=False, progress=False)
        if df is None or df.empty:
            print(f"[WARN] empty data: {tkr}")
            continue
        df.index.name = "date"
        df.to_parquet(f"data/raw/{tkr}.parquet")

    print("[OK] download finished")

if __name__ == "__main__":
    main()

