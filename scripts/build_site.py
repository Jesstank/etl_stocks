from pathlib import Path
from datetime import datetime, timezone
import shutil

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SITE_DIR = BASE_DIR / "site"
SITE_FIGURES_DIR = SITE_DIR / "figures"


def reset_site_folder():
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    SITE_FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def copy_figures():
    if not FIGURES_DIR.exists():
        print("Warning: reports/figures folder does not exist.")
        return

    for figure_path in FIGURES_DIR.glob("*.png"):
        shutil.copy(figure_path, SITE_FIGURES_DIR / figure_path.name)


def read_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)
    return None


def dataframe_to_html(df):
    if df is None or df.empty:
        return "<p class='warning'>Data not available.</p>"

    return df.to_html(
        index=False,
        classes="data-table",
        border=0
    )


def chart_html(title, filename, description):
    figure_path = FIGURES_DIR / filename

    if not figure_path.exists():
        return f"""
        <section>
            <h2>{title}</h2>
            <p class="warning">Chart not available: {filename}</p>
        </section>
        """

    return f"""
    <section>
        <h2>{title}</h2>
        <p class="section-note">{description}</p>
        <img src="figures/{filename}" alt="{title}">
    </section>
    """


def build_html_page():
    updated_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    ticker_summary_path = REPORTS_DIR / "ticker_summary.csv"
    model_results_path = REPORTS_DIR / "factor_timesfm_model_results.csv"
    feature_importance_path = REPORTS_DIR / "factor_timesfm_feature_importance.csv"

    ticker_summary = read_csv_if_exists(ticker_summary_path)
    model_results = read_csv_if_exists(model_results_path)
    feature_importance = read_csv_if_exists(feature_importance_path)

    if model_results is not None and not model_results.empty:
        model_results = model_results.sort_values(
            ["directional_accuracy", "mae"],
            ascending=[False, True]
        )

    if feature_importance is not None and not feature_importance.empty:
        feature_importance = feature_importance.sort_values(
            "importance",
            ascending=False
        ).head(15)

    ticker_summary_html = dataframe_to_html(ticker_summary)
    model_results_html = dataframe_to_html(model_results)
    feature_importance_html = dataframe_to_html(feature_importance)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ETL Stocks Dashboard</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f6f8fa;
            color: #24292f;
        }}

        .container {{
            max-width: 1200px;
            margin: auto;
            background-color: white;
            padding: 32px;
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
        }}

        h1 {{
            margin-bottom: 8px;
        }}

        h2 {{
            margin-top: 42px;
            border-bottom: 2px solid #d0d7de;
            padding-bottom: 8px;
        }}

        h3 {{
            margin-top: 28px;
        }}

        .subtitle {{
            color: #57606a;
            margin-bottom: 24px;
            font-size: 16px;
        }}

        .badge {{
            display: inline-block;
            background-color: #0969da;
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 14px;
            margin-right: 6px;
            margin-bottom: 6px;
        }}

        .highlight-box {{
            background-color: #f6f8fa;
            border-left: 5px solid #0969da;
            padding: 16px;
            margin-top: 18px;
            border-radius: 6px;
        }}

        .warning {{
            color: #bf8700;
            font-weight: bold;
        }}

        .data-table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 16px;
            font-size: 14px;
        }}

        .data-table th {{
            background-color: #24292f;
            color: white;
            padding: 10px;
            text-align: left;
        }}

        .data-table td {{
            padding: 10px;
            border-bottom: 1px solid #d0d7de;
        }}

        .data-table tr:nth-child(even) {{
            background-color: #f6f8fa;
        }}

        img {{
            max-width: 100%;
            border: 1px solid #d0d7de;
            border-radius: 8px;
            margin-top: 16px;
        }}

        .section-note {{
            color: #57606a;
        }}

        .footer {{
            margin-top: 44px;
            color: #57606a;
            font-size: 14px;
            border-top: 1px solid #d0d7de;
            padding-top: 16px;
        }}

        code {{
            background-color: #f6f8fa;
            padding: 2px 5px;
            border-radius: 4px;
        }}

        ul {{
            line-height: 1.6;
        }}
    </style>
</head>

<body>
    <div class="container">
        <h1>ETL_STOCKS: Energy Stock ETL, Forecasting, and Model Comparison</h1>

        <p class="subtitle">
            Automated financial data pipeline using Python, SQLite, TimesFM, machine learning, GitHub Actions, and GitHub Pages.
        </p>

        <p>
            <span class="badge">ETL</span>
            <span class="badge">SQLite</span>
            <span class="badge">TimesFM</span>
            <span class="badge">Machine Learning</span>
            <span class="badge">GitHub Actions</span>
            <span class="badge">GitHub Pages</span>
        </p>

        <section>
            <h2>Project Summary</h2>
            <p>
                This project builds an end-to-end ETL and forecasting pipeline for major U.S. energy stocks:
                <strong>XOM</strong>, <strong>CVX</strong>, and <strong>OXY</strong>.
                It extracts stock market data, engineers financial features, runs TimesFM rolling backtests,
                and compares factor-only, TimesFM-only, and factor-plus-TimesFM machine learning models.
            </p>

            <div class="highlight-box">
                <strong>Current finding:</strong>
                Factor-only tree-based models showed the strongest directional accuracy in the current test window.
                TimesFM forecast features did not improve performance over the factor-only models in the current setup.
            </div>
        </section>

        <section>
            <h2>Pipeline Architecture</h2>
            <p class="section-note">
                The project follows a modular financial data workflow.
            </p>

            <ul>
                <li><strong>Extract:</strong> Download stock and market factor data using yfinance.</li>
                <li><strong>Transform:</strong> Clean data and engineer technical and market features.</li>
                <li><strong>Load:</strong> Store processed data in SQLite.</li>
                <li><strong>Forecast:</strong> Run TimesFM rolling backtest using historical close prices.</li>
                <li><strong>Model:</strong> Compare factor-only, TimesFM-only, and factor-plus-TimesFM models.</li>
                <li><strong>Publish:</strong> Generate static dashboard and deploy with GitHub Pages.</li>
            </ul>
        </section>

        <section>
            <h2>Stock Summary</h2>
            <p class="section-note">
                Summary statistics for the selected energy stocks.
            </p>
            {ticker_summary_html}
        </section>

        {chart_html(
            "Close Price Trend",
            "close_price_trend.png",
            "Historical close price trend for XOM, CVX, and OXY."
        )}

        {chart_html(
            "Normalized Price Trend",
            "normalized_price_trend.png",
            "Each stock starts at 100, allowing relative performance comparison."
        )}

        {chart_html(
            "Daily Return Distribution",
            "daily_return_distribution.png",
            "Distribution of daily returns across selected energy stocks."
        )}

        <section>
            <h2>Final Model Comparison</h2>
            <p class="section-note">
                Models were evaluated by MAE, RMSE, and directional accuracy.
                The baseline assumes zero future return.
            </p>
            {model_results_html}
        </section>

        {chart_html(
            "Model Comparison by MAE",
            "factor_timesfm_model_comparison_mae.png",
            "Lower MAE indicates better return prediction accuracy."
        )}

        {chart_html(
            "Model Comparison by Directional Accuracy",
            "factor_timesfm_model_comparison_direction.png",
            "Directional accuracy measures whether the model correctly predicts up or down movement."
        )}

        <section>
            <h2>Feature Importance</h2>
            <p class="section-note">
                Top features from the factor-plus-TimesFM random forest model.
            </p>
            {feature_importance_html}
        </section>

        {chart_html(
            "Factor + TimesFM Feature Importance",
            "factor_timesfm_feature_importance.png",
            "Feature importance from the random forest model using market factors and TimesFM forecast features."
        )}

        <section>
            <h2>中文说明</h2>
            <p>
                这个项目是一个能源股票 ETL、预测和模型比较项目。项目会自动抓取 XOM、CVX、OXY 的历史股票数据，
                构建 WTI、SPY、XLE、VIX 等市场因子，并使用 TimesFM 进行 rolling backtest。
            </p>

            <p>
                当前结果显示，factor-only 的树模型在方向预测上表现最好；TimesFM 特征在当前设置下没有明显提升模型表现。
                这说明短期股票收益率非常 noisy，必须通过 baseline 和 backtest 进行真实评估。
            </p>
        </section>

        <section>
            <h2>Disclaimer</h2>
            <p>
                This project is for educational and portfolio purposes only.
                It is not financial advice and should not be used as a trading system.
            </p>
        </section>

        <div class="footer">
            Last updated: {updated_time}
        </div>
    </div>
</body>
</html>
"""

    index_path = SITE_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")

    print(f"Site generated at: {index_path}")


def main():
    print("Building GitHub Pages site...")

    reset_site_folder()
    copy_figures()
    build_html_page()

    print("Site build completed successfully.")


if __name__ == "__main__":
    main()