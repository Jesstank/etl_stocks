from pathlib import Path
from datetime import datetime, timezone
import shutil

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SITE_DIR = BASE_DIR / "site"
SITE_FIGURES_DIR = SITE_DIR / "figures"

SUMMARY_PATH = REPORTS_DIR / "ticker_summary.csv"


def reset_site_folder():
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    SITE_FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def copy_figures():
    for figure_path in FIGURES_DIR.glob("*.png"):
        shutil.copy(figure_path, SITE_FIGURES_DIR / figure_path.name)


def build_html_page():
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Summary file not found: {SUMMARY_PATH}")

    summary_df = pd.read_csv(SUMMARY_PATH)

    summary_table_html = summary_df.to_html(
        index=False,
        classes="summary-table",
        border=0
    )

    updated_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

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
            margin-top: 40px;
            border-bottom: 2px solid #d0d7de;
            padding-bottom: 8px;
        }}

        .subtitle {{
            color: #57606a;
            margin-bottom: 24px;
        }}

        .badge {{
            display: inline-block;
            background-color: #0969da;
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 14px;
            margin-right: 6px;
        }}

        .summary-table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 16px;
            font-size: 14px;
        }}

        .summary-table th {{
            background-color: #24292f;
            color: white;
            padding: 10px;
            text-align: left;
        }}

        .summary-table td {{
            padding: 10px;
            border-bottom: 1px solid #d0d7de;
        }}

        .summary-table tr:nth-child(even) {{
            background-color: #f6f8fa;
        }}

        img {{
            max-width: 100%;
            border: 1px solid #d0d7de;
            border-radius: 8px;
            margin-top: 16px;
        }}

        .footer {{
            margin-top: 40px;
            color: #57606a;
            font-size: 14px;
        }}

        .section-note {{
            color: #57606a;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ETL_STOCKS: Energy Stock Market Dashboard</h1>
        <p class="subtitle">
            Automated ETL pipeline report generated from Python, SQLite, Pandas, Matplotlib, and GitHub Actions.
        </p>

        <p>
            <span class="badge">ETL</span>
            <span class="badge">SQLite</span>
            <span class="badge">GitHub Actions</span>
            <span class="badge">GitHub Pages</span>
        </p>

        <h2>Project Overview</h2>
        <p>
            This dashboard tracks selected energy stocks including XOM, CVX, and OXY.
            The pipeline extracts historical market data, transforms it into analysis-ready format,
            loads the data into a SQLite database, and generates financial summary reports and charts.
        </p>

        <h2>Summary Table</h2>
        <p class="section-note">
            This table summarizes stock performance, daily return, volatility, volume, and total return.
        </p>
        {summary_table_html}

        <h2>Close Price Trend</h2>
        <p class="section-note">
            Historical close price trend for each selected energy stock.
        </p>
        <img src="figures/close_price_trend.png" alt="Close Price Trend">

        <h2>Normalized Price Trend</h2>
        <p class="section-note">
            Each stock starts at 100, allowing relative performance comparison.
        </p>
        <img src="figures/normalized_price_trend.png" alt="Normalized Price Trend">

        <h2>Daily Return Distribution</h2>
        <p class="section-note">
            Distribution of daily returns, useful for comparing volatility and risk.
        </p>
        <img src="figures/daily_return_distribution.png" alt="Daily Return Distribution">

        <h2>中文说明</h2>
        <p>
            这个网页是由 GitHub Actions 自动生成的能源股票 ETL 报表。
            Pipeline 会自动抓取 XOM、CVX、OXY 的历史股票数据，清洗后写入 SQLite 数据库，
            并生成 summary table 和可视化图表。
        </p>

        <p>
            这个项目展示了端到端数据工程流程：
            数据提取、数据清洗、数据库加载、SQL 验证、报表生成和静态网页部署。
        </p>

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