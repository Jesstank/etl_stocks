from pathlib import Path
import sqlite3

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Factor settings
# -----------------------------
FACTOR_TICKERS = {
    "wti": "CL=F",
    "spy": "SPY",
    "xle": "XLE",
    "vix": "^VIX",
}


# -----------------------------
# Load stock data
# -----------------------------
def load_stock_data():
    print("Loading stock data from SQLite...")

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
    FROM stock_prices
    ORDER BY ticker, Date;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"])

    print(f"Loaded {len(df)} stock rows.")
    return df


# -----------------------------
# Download external factor data
# -----------------------------
def download_factor_data(start_date, end_date=None):
    print("Downloading factor data...")

    factor_frames = []

    for factor_name, yahoo_ticker in FACTOR_TICKERS.items():
        print(f"Downloading {factor_name}: {yahoo_ticker}")

        df = yf.download(
            yahoo_ticker,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=False,
        )

        if df.empty:
            print(f"Warning: no data downloaded for {factor_name}")
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])

        df = df[["Date", "Close"]].copy()
        df = df.rename(columns={"Close": f"{factor_name}_close"})

        factor_frames.append(df)

    if not factor_frames:
        raise ValueError("No factor data downloaded.")

    factors = factor_frames[0]

    for frame in factor_frames[1:]:
        factors = factors.merge(frame, on="Date", how="outer")

    factors = factors.sort_values("Date")

    close_columns = [col for col in factors.columns if col.endswith("_close")]
    factors[close_columns] = factors[close_columns].ffill()

    print(f"Downloaded factor rows: {len(factors)}")
    return factors


# -----------------------------
# Build feature table
# -----------------------------
def build_features(stock_df, factor_df):
    print("Building ML feature table...")

    df = stock_df.merge(factor_df, on="Date", how="left")
    df = df.sort_values(["ticker", "Date"])

    factor_close_columns = [
        "wti_close",
        "spy_close",
        "xle_close",
        "vix_close",
    ]

    # Forward fill factor values within each ticker timeline
    df[factor_close_columns] = (
        df.groupby("ticker")[factor_close_columns]
        .ffill()
        .bfill()
    )

    # Stock-based features
    df["stock_return_1d"] = df.groupby("ticker")["Close"].pct_change()
    df["volume_change_1d"] = df.groupby("ticker")["Volume"].pct_change()

    df["close_to_ma7"] = df["Close"] / df["moving_avg_7d"] - 1
    df["close_to_ma30"] = df["Close"] / df["moving_avg_30d"] - 1

    df["volatility_7d"] = (
        df.groupby("ticker")["stock_return_1d"]
        .transform(lambda x: x.rolling(window=7).std())
    )

    df["volatility_30d"] = (
        df.groupby("ticker")["stock_return_1d"]
        .transform(lambda x: x.rolling(window=30).std())
    )

    # External factor return features
    for factor in ["wti", "spy", "xle", "vix"]:
        close_col = f"{factor}_close"
        return_col = f"{factor}_return_1d"

        df[return_col] = (
            df.groupby("ticker")[close_col]
            .pct_change()
        )

    # Target variables
    df["target_next_close"] = (
        df.groupby("ticker")["Close"]
        .shift(-1)
    )

    df["target_next_day_return"] = (
        df["target_next_close"] / df["Close"] - 1
    )

    df["target_direction"] = (
        df["target_next_day_return"] > 0
    ).astype(int)

    feature_columns = [
        "Date",
        "ticker",
        "Close",
        "Volume",
        "stock_return_1d",
        "volume_change_1d",
        "close_to_ma7",
        "close_to_ma30",
        "volatility_7d",
        "volatility_30d",
        "wti_close",
        "wti_return_1d",
        "spy_close",
        "spy_return_1d",
        "xle_close",
        "xle_return_1d",
        "vix_close",
        "vix_return_1d",
        "target_next_close",
        "target_next_day_return",
        "target_direction",
    ]

    df = df[feature_columns].copy()
    df = df.dropna()

    print(f"Feature table rows: {len(df)}")

    return df


# -----------------------------
# Save features
# -----------------------------
def save_features(feature_df):
    print("Saving feature table...")

    output_path = PROCESSED_DIR / "ml_features.csv"
    feature_df.to_csv(output_path, index=False)

    conn = sqlite3.connect(DB_PATH)

    feature_df.to_sql(
        "ml_features",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(f"Feature CSV saved to: {output_path}")
    print("Feature table saved to SQLite table: ml_features")


# -----------------------------
# Analyze factor correlation
# -----------------------------
def analyze_factor_correlation(feature_df):
    print("Analyzing factor correlation with target...")

    factor_columns = [
        "stock_return_1d",
        "volume_change_1d",
        "close_to_ma7",
        "close_to_ma30",
        "volatility_7d",
        "volatility_30d",
        "wti_return_1d",
        "spy_return_1d",
        "xle_return_1d",
        "vix_return_1d",
    ]

    target_column = "target_next_day_return"

    correlation_rows = []

    # Overall correlation
    for feature in factor_columns:
        corr_value = feature_df[feature].corr(feature_df[target_column])

        correlation_rows.append(
            {
                "ticker": "ALL",
                "feature": feature,
                "target": target_column,
                "correlation": corr_value,
            }
        )

    # Per ticker correlation
    for ticker, group in feature_df.groupby("ticker"):
        for feature in factor_columns:
            corr_value = group[feature].corr(group[target_column])

            correlation_rows.append(
                {
                    "ticker": ticker,
                    "feature": feature,
                    "target": target_column,
                    "correlation": corr_value,
                }
            )

    corr_df = pd.DataFrame(correlation_rows)
    corr_df["correlation"] = corr_df["correlation"].round(6)

    output_path = REPORTS_DIR / "factor_target_correlation.csv"
    corr_df.to_csv(output_path, index=False)

    print(f"Correlation report saved to: {output_path}")
    print(corr_df.head(20))

    return corr_df


# -----------------------------
# Plot correlation
# -----------------------------
def plot_factor_correlation(corr_df):
    print("Creating factor correlation chart...")

    overall_corr = corr_df[corr_df["ticker"] == "ALL"].copy()
    overall_corr = overall_corr.sort_values("correlation")

    plt.figure(figsize=(10, 6))

    plt.barh(
        overall_corr["feature"],
        overall_corr["correlation"]
    )

    plt.title("Feature Correlation with Next-Day Return")
    plt.xlabel("Correlation with target_next_day_return")
    plt.ylabel("Feature")
    plt.grid(True)

    output_path = FIGURES_DIR / "factor_correlation_with_target.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_path}")


# -----------------------------
# Main
# -----------------------------
def main():
    print("Starting factor feature engineering pipeline...")

    stock_df = load_stock_data()

    start_date = stock_df["Date"].min().strftime("%Y-%m-%d")
    factor_df = download_factor_data(start_date=start_date)

    feature_df = build_features(stock_df, factor_df)

    save_features(feature_df)

    corr_df = analyze_factor_correlation(feature_df)
    plot_factor_correlation(corr_df)

    print("Feature engineering pipeline completed successfully.")


if __name__ == "__main__":
    main()