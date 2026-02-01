import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter


ASSETS_DIR = "assets"
BT_CANDIDATES = [
    "results/backtest_rev_5_step5.csv",
    "results/backtest_rev_5_step5_sample.csv",
]
COST_CANDIDATES = [
    "results/cost_sensitivity_rev_5_step5.csv",
    "results/cost_sensitivity_rev_5_step5_sample.csv",
]


def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def pct_fmt(x, pos=None):
    return f"{x*100:.0f}%"


def pct_fmt_2(x, pos=None):
    return f"{x*100:.2f}%"


def compute_step_stats(bt: pd.DataFrame):
    """
    bt is step=5d backtest with columns: net_ret_5d, equity, drawdown
    Returns annualized stats under step frequency ~252/5 per year
    """
    r = bt["net_ret_5d"].dropna()
    steps_per_year = 252 / 5

    ann_ret = (1.0 + r.mean()) ** steps_per_year - 1.0
    ann_vol = r.std(ddof=1) * np.sqrt(steps_per_year)
    sharpe = ann_ret / ann_vol if ann_vol and not np.isnan(ann_vol) else np.nan
    max_dd = bt["drawdown"].min()
    return ann_ret, ann_vol, sharpe, max_dd


def load_backtest():
    path = _first_existing(BT_CANDIDATES)
    if path is None:
        raise FileNotFoundError("Missing backtest csv. Run scripts/04_backtest.py (step=5d) first.")
    bt = pd.read_csv(path)
    bt["date"] = pd.to_datetime(bt["date"])
    # Normalize expected cols (support either gross_ret_5d/net_ret_5d or already computed)
    if "net_ret_5d" not in bt.columns:
        if "gross_ret_5d" in bt.columns and "cost" in bt.columns:
            bt["net_ret_5d"] = bt["gross_ret_5d"] - bt["cost"]
        else:
            raise ValueError(f"{path} missing net_ret_5d (and cannot infer).")
    if "equity" not in bt.columns:
        bt["equity"] = (1.0 + bt["net_ret_5d"]).cumprod()
    if "drawdown" not in bt.columns:
        bt["drawdown"] = bt["equity"] / bt["equity"].cummax() - 1.0
    return bt, path


def load_cost_sensitivity():
    path = _first_existing(COST_CANDIDATES)
    if path is None:
        return None, None
    cs = pd.read_csv(path)
    # Ensure numeric columns
    for col in ["cost_bps_roundtrip", "sharpe", "ann_ret", "ann_vol", "max_dd"]:
        if col in cs.columns:
            cs[col] = pd.to_numeric(cs[col], errors="coerce")
    return cs, path


def plot_equity(bt: pd.DataFrame, ann_ret, ann_vol, sharpe, max_dd):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(bt["date"], bt["equity"])
    ax.set_title("rev_5 step=5d — Equity Curve (cost-adjusted)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (cum. net)")
    ax.grid(True, alpha=0.3)

    # Year ticks
    ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Small stats box
    txt = f"Sharpe={sharpe:.2f} | AnnRet={ann_ret*100:.2f}% | AnnVol={ann_vol*100:.2f}% | MaxDD={max_dd*100:.2f}%"
    ax.text(
        0.01, 0.98, txt,
        transform=ax.transAxes, ha="left", va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85, edgecolor="none")
    )

    fig.tight_layout()
    fig.savefig(os.path.join(ASSETS_DIR, "equity_rev_5_step5.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_drawdown(bt: pd.DataFrame, max_dd):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(bt["date"], bt["drawdown"])
    ax.set_title("rev_5 step=5d — Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(FuncFormatter(pct_fmt))

    # annotate max drawdown
    dd = bt["drawdown"]
    i = dd.idxmin()
    ax.scatter(bt.loc[i, "date"], bt.loc[i, "drawdown"], s=20)
    ax.text(
        bt.loc[i, "date"], bt.loc[i, "drawdown"],
        f"  MaxDD {max_dd*100:.2f}%",
        va="center", fontsize=9
    )

    fig.tight_layout()
    fig.savefig(os.path.join(ASSETS_DIR, "drawdown_rev_5_step5.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_cost_sensitivity(cs: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    ax.plot(cs["cost_bps_roundtrip"], cs["sharpe"], marker="o")
    ax.set_title("Cost sensitivity — rev_5 step=5d")
    ax.set_xlabel("Round-trip cost (bps)")
    ax.set_ylabel("Sharpe (annualized)")
    ax.grid(True, alpha=0.3)

    # emphasize the zero line
    ax.axhline(0.0, linewidth=1.0, alpha=0.6)

    # annotate key points if present
    for target in [20, 50]:
        if target in set(cs["cost_bps_roundtrip"].dropna().astype(int).tolist()):
            row = cs.loc[cs["cost_bps_roundtrip"] == target].iloc[0]
            ax.scatter([row["cost_bps_roundtrip"]], [row["sharpe"]], s=35)
            ax.text(
                row["cost_bps_roundtrip"], row["sharpe"],
                f"  {target}bps: {row['sharpe']:.2f}",
                fontsize=9, va="center"
            )

    fig.tight_layout()
    fig.savefig(os.path.join(ASSETS_DIR, "cost_sensitivity_sharpe.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    bt, bt_path = load_backtest()
    ann_ret, ann_vol, sharpe, max_dd = compute_step_stats(bt)

    plot_equity(bt, ann_ret, ann_vol, sharpe, max_dd)
    plot_drawdown(bt, max_dd)

    cs, cs_path = load_cost_sensitivity()
    if cs is not None and {"cost_bps_roundtrip", "sharpe"}.issubset(cs.columns):
        plot_cost_sensitivity(cs)

    print("[OK] wrote polished plots to assets/:")
    print(" - assets/equity_rev_5_step5.png")
    print(" - assets/drawdown_rev_5_step5.png")
    if cs is not None:
        print(" - assets/cost_sensitivity_sharpe.png")
    print(f"[INFO] used backtest: {bt_path}")
    if cs_path:
        print(f"[INFO] used cost sensitivity: {cs_path}")


if __name__ == "__main__":
    main()
