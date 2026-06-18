from pathlib import Path
import sqlite3

import pandas as pd
import yfinance as yf


# -----------------------------
# Project settings
# -----------------------------
TICKERS = ["XOM", "CVX", "OXY"]
START_DATE = "2023-01-01"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Extract
# -----------------------------
def extract_stock_data(tickers, start_date):
    all_data = []

    for ticker in tickers:
        print(f"Extracting data for {ticker}...")

        df = yf.download(
            ticker,
            start=start_date,
            progress=False,
            auto_adjust=False
        )

        if df.empty:
            print(f"Warning: No data found for {ticker}")
            continue

        # Handle possible MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df["ticker"] = ticker

        raw_file_path = RAW_DIR / f"{ticker}_raw.csv"
        df.to_csv(raw_file_path, index=False)

        all_data.append(df)

    if not all_data:
        raise ValueError("No stock data was extracted.")

    return pd.concat(all_data, ignore_index=True)


# -----------------------------
# Transform
# -----------------------------
def transform_stock_data(df):
    print("Transforming data...")

    columns_to_keep = [
        "Date",
        "ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume"
    ]

    df = df[columns_to_keep].copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"])

    numeric_columns = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna()

    df["daily_return"] = df.groupby("ticker")["Close"].pct_change()
    df["moving_avg_7d"] = df.groupby("ticker")["Close"].transform(
        lambda x: x.rolling(window=7).mean()
    )
    df["moving_avg_30d"] = df.groupby("ticker")["Close"].transform(
        lambda x: x.rolling(window=30).mean()
    )

    df = df.dropna()

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    processed_file_path = PROCESSED_DIR / "stock_prices_processed.csv"
    df.to_csv(processed_file_path, index=False)

    return df


# -----------------------------
# Load
# -----------------------------
def load_to_sqlite(df):
    print("Loading data into SQLite database...")

    conn = sqlite3.connect(DB_PATH)

    df.to_sql(
        "stock_prices",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(f"Data loaded to database: {DB_PATH}")


# -----------------------------
# Main pipeline
# -----------------------------
def main():
    print("Starting ETL pipeline...")

    raw_data = extract_stock_data(TICKERS, START_DATE)
    processed_data = transform_stock_data(raw_data)
    load_to_sqlite(processed_data)

    print("ETL pipeline completed successfully.")
    print(f"Rows processed: {len(processed_data)}")


if __name__ == "__main__":
    main()