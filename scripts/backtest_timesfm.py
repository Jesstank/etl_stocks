from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import timesfm


# -----------------------------
# Settings
# -----------------------------
TICKERS = ["XOM", "CVX", "OXY"]

MODEL_ID = "google/timesfm-2.5-200m-pytorch"

CONTEXT_LENGTH = 512
HORIZON = 5

# Start small. Increase later if it runs well.
BACKTEST_POINTS_PER_TICKER = 100

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

REPORTS_DIR = BASE_DIR / "reports"
FORECAST_DIR = REPORTS_DIR / "forecast"
FIGURES_DIR = REPORTS_DIR / "figures"

FORECAST_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Load stock data
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
    df = df.sort_values(["ticker", "Date"])

    print(f"Loaded rows: {len(df)}")
    return df


# -----------------------------
# Prepare rolling backtest inputs
# -----------------------------
def prepare_backtest_inputs(df):
    print("Preparing rolling backtest inputs...")

    inputs = []
    metadata = []

    for ticker in TICKERS:
        ticker_df = (
            df[df["ticker"] == ticker]
            .sort_values("Date")
            .reset_index(drop=True)
        )

        if ticker_df.empty:
            print(f"Warning: no data found for {ticker}")
            continue

        min_position = CONTEXT_LENGTH - 1
        max_position = len(ticker_df) - HORIZON - 1

        if max_position <= min_position:
            print(f"Warning: not enough history for {ticker}")
            continue

        candidate_positions = list(range(min_position, max_position + 1))

        # Use most recent N backtest points
        selected_positions = candidate_positions[-BACKTEST_POINTS_PER_TICKER:]

        for position in selected_positions:
            context_series = (
                ticker_df.loc[:position, "Close"]
                .tail(CONTEXT_LENGTH)
                .to_numpy(dtype=np.float32)
            )

            prediction_date = ticker_df.loc[position, "Date"]
            last_close = float(ticker_df.loc[position, "Close"])

            inputs.append(context_series)

            metadata.append(
                {
                    "ticker": ticker,
                    "position": position,
                    "prediction_date": prediction_date,
                    "last_close": last_close,
                    "ticker_df": ticker_df,
                }
            )

        print(f"{ticker}: prepared {len(selected_positions)} backtest points")

    if not inputs:
        raise ValueError("No TimesFM backtest inputs were prepared.")

    print(f"Total TimesFM inputs: {len(inputs)}")
    return inputs, metadata


# -----------------------------
# Load TimesFM model
# -----------------------------
def load_timesfm_model():
    print("Loading TimesFM model...")

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

    print("TimesFM model loaded.")
    return model


# -----------------------------
# Run backtest forecast
# -----------------------------
def run_timesfm_backtest(model, inputs, metadata):
    print("Running TimesFM rolling backtest...")
    print("This may take some time depending on CPU/GPU speed.")

    point_forecast, quantile_forecast = model.forecast(
        horizon=HORIZON,
        inputs=inputs,
    )

    rows = []

    for i, meta in enumerate(metadata):
        ticker = meta["ticker"]
        position = meta["position"]
        prediction_date = meta["prediction_date"]
        last_close = meta["last_close"]
        ticker_df = meta["ticker_df"]

        for step in range(1, HORIZON + 1):
            actual_position = position + step

            actual_date = ticker_df.loc[actual_position, "Date"]
            actual_close = float(ticker_df.loc[actual_position, "Close"])

            timesfm_pred_close = float(point_forecast[i][step - 1])

            timesfm_pred_return = timesfm_pred_close / last_close - 1
            actual_return = actual_close / last_close - 1

            baseline_pred_return = 0.0
            baseline_pred_close = last_close

            timesfm_abs_error_return = abs(timesfm_pred_return - actual_return)
            baseline_abs_error_return = abs(baseline_pred_return - actual_return)

            timesfm_direction = int(timesfm_pred_return > 0)
            actual_direction = int(actual_return > 0)

            rows.append(
                {
                    "ticker": ticker,
                    "prediction_date": prediction_date.strftime("%Y-%m-%d"),
                    "forecast_step": step,
                    "forecast_horizon_days": HORIZON,
                    "actual_date": actual_date.strftime("%Y-%m-%d"),
                    "last_close": last_close,
                    "timesfm_pred_close": timesfm_pred_close,
                    "actual_close": actual_close,
                    "timesfm_pred_return": timesfm_pred_return,
                    "actual_return": actual_return,
                    "baseline_pred_close": baseline_pred_close,
                    "baseline_pred_return": baseline_pred_return,
                    "timesfm_abs_error_return": timesfm_abs_error_return,
                    "baseline_abs_error_return": baseline_abs_error_return,
                    "timesfm_direction": timesfm_direction,
                    "actual_direction": actual_direction,
                    "direction_correct": int(timesfm_direction == actual_direction),
                    "timesfm_beats_baseline": int(
                        timesfm_abs_error_return < baseline_abs_error_return
                    ),
                    "model": "TimesFM 2.5 200M PyTorch",
                    "input_factor": "Close price only",
                    "context_length": len(inputs[i]),
                }
            )

    backtest_df = pd.DataFrame(rows)

    output_path = FORECAST_DIR / "timesfm_backtest.csv"
    backtest_df.to_csv(output_path, index=False)

    print(f"Backtest results saved to: {output_path}")
    print(backtest_df.head())

    return backtest_df


# -----------------------------
# Create metrics
# -----------------------------
def create_backtest_metrics(backtest_df):
    print("Creating backtest metrics...")

    metrics = (
        backtest_df
        .groupby("forecast_step")
        .agg(
            sample_count=("direction_correct", "count"),
            timesfm_mae_return=("timesfm_abs_error_return", "mean"),
            baseline_mae_return=("baseline_abs_error_return", "mean"),
            directional_accuracy=("direction_correct", "mean"),
            timesfm_beats_baseline_rate=("timesfm_beats_baseline", "mean"),
        )
        .reset_index()
    )

    metrics["timesfm_mae_return"] = metrics["timesfm_mae_return"].round(6)
    metrics["baseline_mae_return"] = metrics["baseline_mae_return"].round(6)
    metrics["directional_accuracy"] = metrics["directional_accuracy"].round(4)
    metrics["timesfm_beats_baseline_rate"] = (
        metrics["timesfm_beats_baseline_rate"].round(4)
    )

    output_path = FORECAST_DIR / "timesfm_backtest_metrics.csv"
    metrics.to_csv(output_path, index=False)

    print(f"Backtest metrics saved to: {output_path}")
    print(metrics)

    return metrics


# -----------------------------
# Save to SQLite
# -----------------------------
def save_to_sqlite(backtest_df, metrics_df):
    print("Saving TimesFM backtest results to SQLite...")

    conn = sqlite3.connect(DB_PATH)

    backtest_df.to_sql(
        "timesfm_backtest",
        conn,
        if_exists="replace",
        index=False
    )

    metrics_df.to_sql(
        "timesfm_backtest_metrics",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print("Saved SQLite tables: timesfm_backtest, timesfm_backtest_metrics")


# -----------------------------
# Plot directional accuracy
# -----------------------------
def plot_directional_accuracy(metrics_df):
    print("Creating directional accuracy chart...")

    plt.figure(figsize=(10, 6))

    plt.bar(
        metrics_df["forecast_step"],
        metrics_df["directional_accuracy"]
    )

    plt.axhline(
        y=0.5,
        linestyle="--",
        label="Random Guess 50%"
    )

    plt.title("TimesFM Directional Accuracy by Forecast Step")
    plt.xlabel("Forecast Step")
    plt.ylabel("Directional Accuracy")
    plt.xticks(metrics_df["forecast_step"])
    plt.legend()
    plt.grid(True)

    output_path = FIGURES_DIR / "timesfm_backtest_directional_accuracy.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_path}")


# -----------------------------
# Plot TimesFM error vs baseline
# -----------------------------
def plot_error_vs_baseline(metrics_df):
    print("Creating error vs baseline chart...")

    plt.figure(figsize=(10, 6))

    plt.plot(
        metrics_df["forecast_step"],
        metrics_df["timesfm_mae_return"],
        marker="o",
        label="TimesFM MAE"
    )

    plt.plot(
        metrics_df["forecast_step"],
        metrics_df["baseline_mae_return"],
        marker="o",
        label="Zero Return Baseline MAE"
    )

    plt.title("TimesFM Return MAE vs Zero-Return Baseline")
    plt.xlabel("Forecast Step")
    plt.ylabel("MAE of Return")
    plt.xticks(metrics_df["forecast_step"])
    plt.legend()
    plt.grid(True)

    output_path = FIGURES_DIR / "timesfm_backtest_error_vs_baseline.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_path}")


# -----------------------------
# Main
# -----------------------------
def main():
    print("Starting TimesFM rolling backtest...")

    df = load_stock_data()
    inputs, metadata = prepare_backtest_inputs(df)

    model = load_timesfm_model()

    backtest_df = run_timesfm_backtest(model, inputs, metadata)
    metrics_df = create_backtest_metrics(backtest_df)

    save_to_sqlite(backtest_df, metrics_df)

    plot_directional_accuracy(metrics_df)
    plot_error_vs_baseline(metrics_df)

    print("TimesFM rolling backtest completed successfully.")


if __name__ == "__main__":
    main()