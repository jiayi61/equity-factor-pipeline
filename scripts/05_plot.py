import os
import pandas as pd
import matplotlib.pyplot as plt


ASSETS_DIR = "assets"
BT_PATH = "results/backtest_rev_5_step5.csv"
COST_PATH = "results/cost_sensitivity_rev_5_step5.csv"


def plot_equity_and_drawdown(bt: pd.DataFrame):
    bt = bt.copy()
    bt["date"] = pd.to_datetime(bt["date"])

    # equity curve
    plt.figure()
    plt.plot(bt["date"], bt["equity"])
    plt.xlabel("Date")
    plt.ylabel("Equity (cum. net)")
    plt.title("rev_5 step=5d — Equity Curve (cost-adjusted)")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "equity_rev_5_step5.png"), dpi=160)
    plt.close()

    # drawdown
    plt.figure()
    plt.plot(bt["date"], bt["drawdown"])
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.title("rev_5 step=5d — Drawdown")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "drawdown_rev_5_step5.png"), dpi=160)
    plt.close()


def plot_cost_sensitivity(cost: pd.DataFrame):
    cost = cost.copy()
    # expects columns: cost_bps_roundtrip, sharpe, ann_ret (from your csv)
    if "ann_ret" in cost.columns and cost["ann_ret"].dtype != "float":
        # if already formatted as strings, don't plot ann_ret
        pass

    plt.figure()
    plt.plot(cost["cost_bps_roundtrip"], cost["sharpe"], marker="o")
    plt.xlabel("Round-trip cost (bps)")
    plt.ylabel("Sharpe (annualized)")
    plt.title("Cost sensitivity — rev_5 step=5d")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "cost_sensitivity_sharpe.png"), dpi=160)
    plt.close()


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    if not os.path.exists(BT_PATH):
        raise FileNotFoundError(f"Missing {BT_PATH}. Run scripts/04_backtest.py (step=5d) first.")
    bt = pd.read_csv(BT_PATH)

    # Ensure required cols exist
    for col in ["date", "equity", "drawdown"]:
        if col not in bt.columns:
            raise ValueError(f"{BT_PATH} missing column: {col}")

    plot_equity_and_drawdown(bt)

    if os.path.exists(COST_PATH):
        cost = pd.read_csv(COST_PATH)
        if {"cost_bps_roundtrip", "sharpe"}.issubset(cost.columns):
            plot_cost_sensitivity(cost)

    print("[OK] wrote plots to assets/:")
    print(" - assets/equity_rev_5_step5.png")
    print(" - assets/drawdown_rev_5_step5.png")
    if os.path.exists(COST_PATH):
        print(" - assets/cost_sensitivity_sharpe.png")


if __name__ == "__main__":
    main()
