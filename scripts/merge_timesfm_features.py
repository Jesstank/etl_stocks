from pathlib import Path
import sqlite3

import pandas as pd


# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
FORECAST_DIR = REPORTS_DIR / "forecast"

ML_FEATURES_PATH = PROCESSED_DIR / "ml_features.csv"
TIMESFM_BACKTEST_PATH = FORECAST_DIR / "timesfm_backtest.csv"

OUTPUT_PATH = PROCESSED_DIR / "ml_features_with_timesfm.csv"


# -----------------------------
# Load files
# -----------------------------
def load_data():
    print("Loading ML features and TimesFM backtest results...")

    if not ML_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"ML feature file not found: {ML_FEATURES_PATH}. "
            "Run scripts/build_features.py first."
        )

    if not TIMESFM_BACKTEST_PATH.exists():
        raise FileNotFoundError(
            f"TimesFM backtest file not found: {TIMESFM_BACKTEST_PATH}. "
            "Run scripts/backtest_timesfm.py first."
        )

    ml_df = pd.read_csv(ML_FEATURES_PATH)
    timesfm_df = pd.read_csv(TIMESFM_BACKTEST_PATH)

    ml_df["Date"] = pd.to_datetime(ml_df["Date"])
    timesfm_df["prediction_date"] = pd.to_datetime(timesfm_df["prediction_date"])

    print(f"ML features rows: {len(ml_df)}")
    print(f"TimesFM backtest rows: {len(timesfm_df)}")

    return ml_df, timesfm_df


# -----------------------------
# Convert TimesFM backtest to feature table
# -----------------------------
def build_timesfm_feature_table(timesfm_df):
    print("Building TimesFM feature table...")

    # Only use prediction outputs.
    # Do NOT use actual_return, direction_correct, or timesfm_beats_baseline as features.
    safe_columns = [
        "ticker",
        "prediction_date",
        "forecast_step",
        "timesfm_pred_return",
        "timesfm_pred_close",
        "timesfm_direction",
    ]

    timesfm_df = timesfm_df[safe_columns].copy()

    # Pivot predicted returns
    return_wide = timesfm_df.pivot_table(
        index=["ticker", "prediction_date"],
        columns="forecast_step",
        values="timesfm_pred_return",
        aggfunc="first",
    )

    return_wide.columns = [
        f"timesfm_pred_return_step{int(col)}"
        for col in return_wide.columns
    ]

    # Pivot predicted close prices
    close_wide = timesfm_df.pivot_table(
        index=["ticker", "prediction_date"],
        columns="forecast_step",
        values="timesfm_pred_close",
        aggfunc="first",
    )

    close_wide.columns = [
        f"timesfm_pred_close_step{int(col)}"
        for col in close_wide.columns
    ]

    # Pivot predicted directions
    direction_wide = timesfm_df.pivot_table(
        index=["ticker", "prediction_date"],
        columns="forecast_step",
        values="timesfm_direction",
        aggfunc="first",
    )

    direction_wide.columns = [
        f"timesfm_direction_step{int(col)}"
        for col in direction_wide.columns
    ]

    # Combine
    timesfm_features = pd.concat(
        [return_wide, close_wide, direction_wide],
        axis=1
    ).reset_index()

    # Rename for merge
    timesfm_features = timesfm_features.rename(
        columns={"prediction_date": "Date"}
    )

    # Add derived TimesFM features
    if (
        "timesfm_pred_return_step1" in timesfm_features.columns
        and "timesfm_pred_return_step5" in timesfm_features.columns
    ):
        timesfm_features["timesfm_pred_return_slope_1_to_5"] = (
            timesfm_features["timesfm_pred_return_step5"]
            - timesfm_features["timesfm_pred_return_step1"]
        )

    print(f"TimesFM feature rows: {len(timesfm_features)}")
    print(timesfm_features.head())

    return timesfm_features


# -----------------------------
# Merge with ML features
# -----------------------------
def merge_features(ml_df, timesfm_features):
    print("Merging regular factors with TimesFM features...")

    merged_df = ml_df.merge(
        timesfm_features,
        on=["Date", "ticker"],
        how="inner"
    )

    print(f"Rows after merge: {len(merged_df)}")

    if merged_df.empty:
        raise ValueError(
            "Merged feature table is empty. "
            "Check whether Date and ticker match between ml_features and TimesFM backtest."
        )

    return merged_df


# -----------------------------
# Save output
# -----------------------------
def save_output(merged_df):
    print("Saving merged feature table...")

    merged_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved CSV to: {OUTPUT_PATH}")

    conn = sqlite3.connect(DB_PATH)

    merged_df.to_sql(
        "ml_features_with_timesfm",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print("Saved SQLite table: ml_features_with_timesfm")


# -----------------------------
# Main
# -----------------------------
def main():
    print("Starting TimesFM feature merge pipeline...")

    ml_df, timesfm_df = load_data()
    timesfm_features = build_timesfm_feature_table(timesfm_df)
    merged_df = merge_features(ml_df, timesfm_features)
    save_output(merged_df)

    print("TimesFM feature merge completed successfully.")


if __name__ == "__main__":
    main()