from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "etl_stocks.db"

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

INPUT_PATH = PROCESSED_DIR / "ml_features_with_timesfm.csv"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Target
# -----------------------------
TARGET_COLUMN = "target_next_day_return"


# -----------------------------
# Base factor features
# -----------------------------
FACTOR_FEATURES = [
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


# -----------------------------
# Load data
# -----------------------------
def load_data():
    print("Loading merged factor + TimesFM feature data...")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run scripts/merge_timesfm_features.py first."
        )

    df = pd.read_csv(INPUT_PATH)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "ticker"])

    print(f"Loaded rows: {len(df)}")
    print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

    return df


# -----------------------------
# Prepare data
# -----------------------------
def prepare_data(df):
    print("Preparing modeling dataset...")

    df = df.copy()
    df["ticker_original"] = df["ticker"]

    df_model = pd.get_dummies(
        df,
        columns=["ticker"],
        prefix="ticker_dummy",
        drop_first=False
    )

    ticker_features = [
        col for col in df_model.columns
        if col.startswith("ticker_dummy_")
    ]

    df_model[ticker_features] = df_model[ticker_features].astype(int)

    timesfm_features = [
        col for col in df_model.columns
        if col.startswith("timesfm_pred_return_step")
        or col.startswith("timesfm_direction_step")
        or col == "timesfm_pred_return_slope_1_to_5"
    ]

    # Avoid raw TimesFM predicted close as feature for now.
    # It is price-level and can be scale-sensitive.
    feature_sets = {
        "factor_only": FACTOR_FEATURES + ticker_features,
        "timesfm_only": timesfm_features + ticker_features,
        "factor_plus_timesfm": FACTOR_FEATURES + timesfm_features + ticker_features,
    }

    required_columns = list(
        set(
            FACTOR_FEATURES
            + timesfm_features
            + ticker_features
            + [TARGET_COLUMN]
        )
    )

    df_model = df_model.dropna(subset=required_columns)

    # Time-based split, no random split
    unique_dates = sorted(df_model["Date"].unique())
    split_index = int(len(unique_dates) * 0.8)
    split_date = unique_dates[split_index]

    train_df = df_model[df_model["Date"] < split_date].copy()
    test_df = df_model[df_model["Date"] >= split_date].copy()

    print(f"Train rows: {len(train_df)}")
    print(f"Test rows: {len(test_df)}")
    print(f"Split date: {pd.Timestamp(split_date).strftime('%Y-%m-%d')}")
    print(f"Factor features: {len(FACTOR_FEATURES)}")
    print(f"TimesFM features: {len(timesfm_features)}")
    print(f"Ticker dummy features: {len(ticker_features)}")

    return train_df, test_df, feature_sets


# -----------------------------
# Models
# -----------------------------
def get_models():
    models = {
        "linear_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("model", LinearRegression()),
            ]
        ),

        "random_forest": RandomForestRegressor(
            n_estimators=300,
            max_depth=4,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),

        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.03,
            max_depth=2,
            random_state=42,
        ),
    }

    return models


# -----------------------------
# Evaluation
# -----------------------------
def evaluate_predictions(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    actual_direction = y_true > 0
    predicted_direction = y_pred > 0

    directional_accuracy = (
        actual_direction == predicted_direction
    ).mean()

    return mae, rmse, directional_accuracy


# -----------------------------
# Train and compare
# -----------------------------
def train_and_compare(train_df, test_df, feature_sets):
    print("Training and comparing feature sets...")

    results = []
    predictions = []

    y_train = train_df[TARGET_COLUMN]
    y_test = test_df[TARGET_COLUMN]

    # Baseline: predict zero return
    baseline_pred = np.zeros(len(y_test))
    baseline_mae, baseline_rmse, baseline_dir_acc = evaluate_predictions(
        y_test,
        baseline_pred
    )

    results.append(
        {
            "feature_set": "baseline",
            "model": "zero_return",
            "mae": baseline_mae,
            "rmse": baseline_rmse,
            "directional_accuracy": baseline_dir_acc,
        }
    )

    models = get_models()
    fitted_models = {}

    for feature_set_name, feature_columns in feature_sets.items():
        print(f"\nFeature set: {feature_set_name}")
        print(f"Number of features: {len(feature_columns)}")

        X_train = train_df[feature_columns]
        X_test = test_df[feature_columns]

        for model_name, model in models.items():
            print(f"Training model: {model_name}")

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            mae, rmse, dir_acc = evaluate_predictions(y_test, y_pred)

            results.append(
                {
                    "feature_set": feature_set_name,
                    "model": model_name,
                    "mae": mae,
                    "rmse": rmse,
                    "directional_accuracy": dir_acc,
                }
            )

            fitted_models[(feature_set_name, model_name)] = model

            pred_df = test_df[
                ["Date", "ticker_original", TARGET_COLUMN]
            ].copy()

            pred_df = pred_df.rename(columns={"ticker_original": "ticker"})
            pred_df["feature_set"] = feature_set_name
            pred_df["model"] = model_name
            pred_df["prediction"] = y_pred
            pred_df["actual_direction"] = pred_df[TARGET_COLUMN] > 0
            pred_df["predicted_direction"] = pred_df["prediction"] > 0

            predictions.append(pred_df)

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(["mae", "directional_accuracy"])

    predictions_df = pd.concat(predictions, ignore_index=True)

    return results_df, predictions_df, fitted_models


# -----------------------------
# Save results
# -----------------------------
def save_results(results_df, predictions_df):
    print("Saving results...")

    results_path = REPORTS_DIR / "factor_timesfm_model_results.csv"
    predictions_path = REPORTS_DIR / "factor_timesfm_predictions.csv"

    results_df.to_csv(results_path, index=False)
    predictions_df.to_csv(predictions_path, index=False)

    conn = sqlite3.connect(DB_PATH)

    results_df.to_sql(
        "factor_timesfm_model_results",
        conn,
        if_exists="replace",
        index=False
    )

    predictions_df.to_sql(
        "factor_timesfm_predictions",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(f"Results saved to: {results_path}")
    print(f"Predictions saved to: {predictions_path}")


# -----------------------------
# Plot model comparison
# -----------------------------
def plot_model_comparison(results_df):
    print("Creating model comparison charts...")

    plot_df = results_df.copy()
    plot_df["label"] = plot_df["feature_set"] + " | " + plot_df["model"]

    plot_df = plot_df.sort_values("mae")

    plt.figure(figsize=(12, 7))
    plt.barh(plot_df["label"], plot_df["mae"])

    plt.title("Model Comparison by MAE")
    plt.xlabel("MAE")
    plt.ylabel("Feature Set | Model")
    plt.grid(True)

    output_path = FIGURES_DIR / "factor_timesfm_model_comparison_mae.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"MAE chart saved to: {output_path}")

    plot_df = results_df.copy()
    plot_df["label"] = plot_df["feature_set"] + " | " + plot_df["model"]
    plot_df = plot_df.sort_values("directional_accuracy")

    plt.figure(figsize=(12, 7))
    plt.barh(plot_df["label"], plot_df["directional_accuracy"])

    plt.axvline(
        x=0.5,
        linestyle="--",
        label="Random Guess 50%"
    )

    plt.title("Model Comparison by Directional Accuracy")
    plt.xlabel("Directional Accuracy")
    plt.ylabel("Feature Set | Model")
    plt.legend()
    plt.grid(True)

    output_path = FIGURES_DIR / "factor_timesfm_model_comparison_direction.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Directional accuracy chart saved to: {output_path}")


# -----------------------------
# Feature importance
# -----------------------------
def plot_feature_importance(fitted_models, feature_sets):
    print("Creating feature importance chart...")

    key = ("factor_plus_timesfm", "random_forest")

    if key not in fitted_models:
        print("Random forest factor_plus_timesfm model not found.")
        return

    model = fitted_models[key]
    feature_columns = feature_sets["factor_plus_timesfm"]

    importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    )

    importance_df = importance_df.sort_values(
        "importance",
        ascending=True
    )

    output_csv = REPORTS_DIR / "factor_timesfm_feature_importance.csv"
    importance_df.to_csv(output_csv, index=False)

    plt.figure(figsize=(10, 8))

    plt.barh(
        importance_df["feature"],
        importance_df["importance"]
    )

    plt.title("Factor + TimesFM Random Forest Feature Importance")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.grid(True)

    output_path = FIGURES_DIR / "factor_timesfm_feature_importance.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Feature importance saved to: {output_csv}")
    print(f"Feature importance chart saved to: {output_path}")


# -----------------------------
# Main
# -----------------------------
def main():
    print("Starting Factor + TimesFM ML model comparison...")

    df = load_data()

    train_df, test_df, feature_sets = prepare_data(df)

    results_df, predictions_df, fitted_models = train_and_compare(
        train_df,
        test_df,
        feature_sets
    )

    print("\nModel comparison results:")
    print(results_df)

    save_results(results_df, predictions_df)

    plot_model_comparison(results_df)
    plot_feature_importance(fitted_models, feature_sets)

    print("Factor + TimesFM ML model comparison completed successfully.")


if __name__ == "__main__":
    main()