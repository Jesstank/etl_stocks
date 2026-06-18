from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Load data from SQLite
# -----------------------------
def load_stock_data():
    print("Loading data from SQLite database...")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        Date,
        ticker,
        Open,
        High,
        Low,
        Close,
        "Adj Close",
        Volume,
        daily_return,
        moving_avg_7d,
        moving_avg_30d
    FROM stock_prices;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"])

    print(f"Loaded {len(df)} rows.")
    return df


# -----------------------------
# Create summary table
# -----------------------------
def create_ticker_summary(df):
    print("Creating ticker summary...")

    summary = (
        df.groupby("ticker")
        .agg(
            row_count=("Date", "count"),
            start_date=("Date", "min"),
            end_date=("Date", "max"),
            start_close=("Close", "first"),
            end_close=("Close", "last"),
            min_close=("Close", "min"),
            max_close=("Close", "max"),
            avg_daily_return=("daily_return", "mean"),
            volatility=("daily_return", "std"),
            avg_volume=("Volume", "mean"),
        )
        .reset_index()
    )

    summary["total_return"] = (
        summary["end_close"] / summary["start_close"] - 1
    )

    # Make output easier to read
    summary["start_date"] = summary["start_date"].dt.strftime("%Y-%m-%d")
    summary["end_date"] = summary["end_date"].dt.strftime("%Y-%m-%d")

    numeric_columns = [
        "start_close",
        "end_close",
        "min_close",
        "max_close",
        "avg_daily_return",
        "volatility",
        "avg_volume",
        "total_return",
    ]

    summary[numeric_columns] = summary[numeric_columns].round(4)

    output_path = REPORTS_DIR / "ticker_summary.csv"
    summary.to_csv(output_path, index=False)

    print(f"Summary saved to: {output_path}")
    print(summary)

    return summary


# -----------------------------
# Plot close price trend
# -----------------------------
def plot_close_price_trend(df):
    print("Creating close price trend chart...")

    pivot_df = df.pivot(
        index="Date",
        columns="ticker",
        values="Close"
    )

    plt.figure(figsize=(12, 6))

    for ticker in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[ticker], label=ticker)

    plt.title("Close Price Trend")
    plt.xlabel("Date")
    plt.ylabel("Close Price")
    plt.legend()
    plt.grid(True)

    output_path = FIGURES_DIR / "close_price_trend.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_path}")


# -----------------------------
# Plot normalized close price trend
# -----------------------------
def plot_normalized_price_trend(df):
    print("Creating normalized price trend chart...")

    df = df.copy()

    df["normalized_close"] = (
        df.groupby("ticker")["Close"]
        .transform(lambda x: x / x.iloc[0] * 100)
    )

    pivot_df = df.pivot(
        index="Date",
        columns="ticker",
        values="normalized_close"
    )

    plt.figure(figsize=(12, 6))

    for ticker in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[ticker], label=ticker)

    plt.title("Normalized Close Price Trend")
    plt.xlabel("Date")
    plt.ylabel("Normalized Price, Start = 100")
    plt.legend()
    plt.grid(True)

    output_path = FIGURES_DIR / "normalized_price_trend.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_path}")


# -----------------------------
# Plot daily return distribution
# -----------------------------
def plot_daily_return_distribution(df):
    print("Creating daily return distribution chart...")

    plt.figure(figsize=(12, 6))

    for ticker, group in df.groupby("ticker"):
        plt.hist(
            group["daily_return"].dropna(),
            bins=50,
            alpha=0.5,
            label=ticker
        )

    plt.title("Daily Return Distribution")
    plt.xlabel("Daily Return")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True)

    output_path = FIGURES_DIR / "daily_return_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_path}")


# -----------------------------
# Main analysis pipeline
# -----------------------------
def main():
    print("Starting database analysis...")

    df = load_stock_data()

    create_ticker_summary(df)
    plot_close_price_trend(df)
    plot_normalized_price_trend(df)
    plot_daily_return_distribution(df)

    print("Analysis completed successfully.")


if __name__ == "__main__":
    main()