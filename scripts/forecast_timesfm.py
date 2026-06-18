from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import timesfm


# -----------------------------
# Project settings
# -----------------------------
TICKERS = ["XOM", "CVX", "OXY"]
HORIZON = 5
CONTEXT_LENGTH = 512

MODEL_ID = "google/timesfm-2.5-200m-pytorch"

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

REPORTS_DIR = BASE_DIR / "reports"
FORECAST_DIR = REPORTS_DIR / "forecast"
FIGURES_DIR = REPORTS_DIR / "figures"

FORECAST_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Load stock data from SQLite
# -----------------------------
def load_stock_data():
    print("Loading stock data from SQLite...")

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run scripts/main.py first."
        )

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        Date,
        ticker,
        Close
    FROM stock_prices
    ORDER BY ticker, Date;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna()

    print(f"Loaded {len(df)} rows.")
    return df


# -----------------------------
# Prepare TimesFM inputs
# -----------------------------
def prepare_timesfm_inputs(df):
    print("Preparing TimesFM input series...")

    inputs = []
    metadata = {}

    for ticker in TICKERS:
        ticker_df = df[df["ticker"] == ticker].sort_values("Date")

        if ticker_df.empty:
            print(f"Warning: No data found for {ticker}")
            continue

        series = ticker_df["Close"].tail(CONTEXT_LENGTH).to_numpy(dtype=np.float32)

        if len(series) < 50:
            print(f"Warning: Not enough data for {ticker}")
            continue

        inputs.append(series)

        metadata[ticker] = {
            "last_date": ticker_df["Date"].max(),
            "history": ticker_df.tail(120).copy(),
        }

        print(f"{ticker}: using {len(series)} historical points")

    if not inputs:
        raise ValueError("No valid input series prepared for TimesFM.")

    return inputs, metadata


# -----------------------------
# Load TimesFM model
# -----------------------------
def load_timesfm_model():
    print("Loading TimesFM model...")
    print("First run may take several minutes because model weights need to be downloaded.")

    torch.set_float32_matmul_precision("high")

    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(MODEL_ID)

    model.compile(
        timesfm.ForecastConfig(
            max_context=CONTEXT_LENGTH,
            max_horizon=HORIZON,
            normalize_inputs=True,
            use_continuous_quantile_head=True,
            force_flip_invariance=True,
            infer_is_positive=True,
            fix_quantile_crossing=True,
        )
    )

    print("TimesFM model loaded successfully.")
    return model


# -----------------------------
# Run forecast
# -----------------------------
def run_forecast(model, inputs, metadata):
    print("Running TimesFM forecast...")

    point_forecast, quantile_forecast = model.forecast(
        horizon=HORIZON,
        inputs=inputs,
    )

    forecast_rows = []

    tickers_used = list(metadata.keys())

    for i, ticker in enumerate(tickers_used):
        last_date = metadata[ticker]["last_date"]

        future_dates = pd.bdate_range(
            start=last_date + pd.Timedelta(days=1),
            periods=HORIZON
        )

        for step, forecast_date in enumerate(future_dates):
            forecast_rows.append(
                {
                    "ticker": ticker,
                    "forecast_date": forecast_date.strftime("%Y-%m-%d"),
                    "forecast_step": step + 1,
                    "forecast_close": float(point_forecast[i][step]),
                    "model": "TimesFM 2.5 200M PyTorch",
                }
            )

    forecast_df = pd.DataFrame(forecast_rows)

    output_path = FORECAST_DIR / "timesfm_forecast.csv"
    forecast_df.to_csv(output_path, index=False)

    print(f"Forecast saved to: {output_path}")
    print(forecast_df)

    return forecast_df


# -----------------------------
# Plot forecast
# -----------------------------
def plot_forecasts(df, forecast_df, metadata):
    print("Creating forecast charts...")

    for ticker in forecast_df["ticker"].unique():
        history_df = metadata[ticker]["history"]
        ticker_forecast = forecast_df[forecast_df["ticker"] == ticker].copy()
        ticker_forecast["forecast_date"] = pd.to_datetime(
            ticker_forecast["forecast_date"]
        )

        plt.figure(figsize=(12, 6))

        plt.plot(
            history_df["Date"],
            history_df["Close"],
            label=f"{ticker} Historical Close"
        )

        plt.plot(
            ticker_forecast["forecast_date"],
            ticker_forecast["forecast_close"],
            linestyle="--",
            marker="o",
            label=f"{ticker} TimesFM Forecast"
        )

        plt.title(f"{ticker} Close Price Forecast with TimesFM")
        plt.xlabel("Date")
        plt.ylabel("Close Price")
        plt.legend()
        plt.grid(True)

        output_path = FIGURES_DIR / f"timesfm_forecast_{ticker}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Chart saved to: {output_path}")


# -----------------------------
# Main
# -----------------------------
def main():
    print("Starting TimesFM forecasting pipeline...")

    df = load_stock_data()
    inputs, metadata = prepare_timesfm_inputs(df)

    model = load_timesfm_model()
    forecast_df = run_forecast(model, inputs, metadata)

    plot_forecasts(df, forecast_df, metadata)

    print("TimesFM forecasting completed successfully.")


if __name__ == "__main__":
    main()