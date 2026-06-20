# ETL_STOCKS: Energy Stock ETL, Forecasting, and Model Comparison

## Project Overview

**ETL_STOCKS** is an end-to-end financial data engineering and forecasting project focused on major U.S. energy stocks. The project builds an automated ETL pipeline, stores structured market data in SQLite, generates analytical reports, applies Google Research's TimesFM model for time-series forecasting, and compares traditional market-factor models against TimesFM-enhanced machine learning models.

The project is designed as a lightweight but complete data pipeline:

```text
Extract market data
        ↓
Transform and engineer features
        ↓
Load data into SQLite
        ↓
Generate reports and charts
        ↓
Run TimesFM rolling backtest
        ↓
Merge TimesFM forecasts with market factors
        ↓
Compare ML models
        ↓
Publish dashboard through GitHub Pages
```

Live dashboard:

```text
https://jesstank.github.io/etl_stocks/
```

---

## Stocks Covered

The current version focuses on three major energy stocks:

| Ticker | Company                          |
| ------ | -------------------------------- |
| XOM    | Exxon Mobil Corporation          |
| CVX    | Chevron Corporation              |
| OXY    | Occidental Petroleum Corporation |

---

## Data Sources

The project uses `yfinance` to collect historical market data.

Main stock data:

```text
XOM
CVX
OXY
```

External market factors:

| Factor                | Ticker | Meaning                        |
| --------------------- | ------ | ------------------------------ |
| WTI crude oil futures | CL=F   | Crude oil price proxy          |
| S&P 500 ETF           | SPY    | Broad U.S. market proxy        |
| Energy sector ETF     | XLE    | Energy sector proxy            |
| VIX index             | ^VIX   | Market volatility / fear index |

---

## Main Components

## 1. ETL Pipeline

The ETL pipeline extracts historical stock data, cleans the data, calculates returns and moving averages, and stores the processed results in a SQLite database.

Main script:

```text
scripts/main.py
```

Generated database:

```text
data/etl_stocks.db
```

Main SQLite table:

```text
stock_prices
```

---

## 2. Analysis Reports

The project generates basic market analysis outputs, including:

```text
reports/ticker_summary.csv
reports/figures/close_price_trend.png
reports/figures/normalized_price_trend.png
reports/figures/daily_return_distribution.png
```

Main script:

```text
scripts/analyze_db.py
```

---

## 3. Feature Engineering

The project builds a machine learning feature table using stock-level technical features and external market factors.

Main script:

```text
scripts/build_features.py
```

Feature groups include:

```text
stock_return_1d
volume_change_1d
close_to_ma7
close_to_ma30
volatility_7d
volatility_30d
wti_return_1d
spy_return_1d
xle_return_1d
vix_return_1d
```

Output:

```text
data/processed/ml_features.csv
```

---

## 4. TimesFM Rolling Backtest

The project uses Google Research's TimesFM model as a zero-shot time-series forecasting model.

In this project, TimesFM is used as a univariate forecasting model:

```text
Input: recent historical close prices
Output: future close price forecast
```

The rolling backtest simulates historical prediction dates. For each prediction date, the model only sees data available up to that point, forecasts the next 5 business days, and compares the forecast with actual future prices.

Main script:

```text
scripts/backtest_timesfm.py
```

Backtest output:

```text
reports/forecast/timesfm_backtest.csv
reports/forecast/timesfm_backtest_metrics.csv
```

---

## 5. Factor + TimesFM Feature Merge

TimesFM forecasts are converted into machine learning features and merged with regular market factors.

Main script:

```text
scripts/merge_timesfm_features.py
```

Merged output:

```text
data/processed/ml_features_with_timesfm.csv
```

TimesFM features include:

```text
timesfm_pred_return_step1
timesfm_pred_return_step2
timesfm_pred_return_step3
timesfm_pred_return_step4
timesfm_pred_return_step5
timesfm_direction_step1
timesfm_direction_step2
timesfm_direction_step3
timesfm_direction_step4
timesfm_direction_step5
timesfm_pred_return_slope_1_to_5
```

---

## 6. Model Comparison

The final modeling step compares three feature settings:

```text
1. factor_only
2. timesfm_only
3. factor_plus_timesfm
```

Models tested:

```text
Linear Regression
Random Forest
Gradient Boosting
Zero-return baseline
```

Main script:

```text
scripts/train_factor_timesfm_model.py
```

Final result files:

```text
reports/factor_timesfm_model_results.csv
reports/factor_timesfm_feature_importance.csv
reports/figures/factor_timesfm_model_comparison_mae.png
reports/figures/factor_timesfm_model_comparison_direction.png
reports/figures/factor_timesfm_feature_importance.png
```

---

## Current Findings

The current test results show that:

```text
Factor-only tree-based models achieved the best directional accuracy.
TimesFM-only features did not consistently outperform the baseline.
Adding TimesFM features did not improve the factor-only model in the current setup.
The zero-return baseline remained strong in MAE because next-day stock returns are noisy and often close to zero.
```

In the latest model comparison, the strongest directional results came from:

```text
factor_only + random_forest
factor_only + gradient_boosting
```

Both reached approximately:

```text
58.33% directional accuracy
```

However, no model consistently outperformed the zero-return baseline in MAE.

This suggests that short-term next-day stock return prediction remains highly noisy. TimesFM may still be useful as a forecasting component, but in the current setup, its forecast features did not provide a stable improvement over traditional factor-only models.

---

## Important Interpretation

This project should not be interpreted as an investment recommendation system.

The goal is not to claim that the model can reliably predict stock prices. Instead, the goal is to build a realistic financial data pipeline and evaluate whether different forecasting approaches provide measurable predictive value.

The current result is valuable because it shows a disciplined modeling process:

```text
Build ETL pipeline
Create features
Run TimesFM forecast
Backtest predictions
Compare models
Evaluate against baseline
Report honest results
```

---

## Project Structure

```text
ETL_STOCKS/
│
├── .github/
│   └── workflows/
│       └── etl.yml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── etl_stocks.db
│
├── reports/
│   ├── factor_timesfm_model_results.csv
│   ├── factor_timesfm_feature_importance.csv
│   │
│   └── figures/
│       ├── close_price_trend.png
│       ├── normalized_price_trend.png
│       ├── daily_return_distribution.png
│       ├── factor_timesfm_model_comparison_mae.png
│       ├── factor_timesfm_model_comparison_direction.png
│       └── factor_timesfm_feature_importance.png
│
├── scripts/
│   ├── main.py
│   ├── check_db.py
│   ├── analyze_db.py
│   ├── build_site.py
│   ├── build_features.py
│   ├── backtest_timesfm.py
│   ├── merge_timesfm_features.py
│   └── train_factor_timesfm_model.py
│
├── requirements.txt
├── requirements-timesfm.txt
├── .gitignore
└── README.md
```

---

## Installation

## Basic ETL Environment

For the basic ETL and dashboard pipeline:

```bash
conda create -n etl-env python=3.11 -y
conda activate etl-env
pip install -r requirements.txt
```

## TimesFM / ML Environment

For TimesFM forecasting and model comparison:

```bash
conda create -n timesfm-env python=3.11 -y
conda activate timesfm-env
pip install -r requirements-timesfm.txt
```

Recommended `requirements-timesfm.txt`:

```text
numpy
pandas
matplotlib
yfinance
scikit-learn
torch
timesfm[torch]
```

---

## How to Run

## 1. Run ETL Pipeline

```bash
python scripts/main.py
```

## 2. Validate SQLite Database

```bash
python scripts/check_db.py
```

## 3. Generate Basic Reports

```bash
python scripts/analyze_db.py
```

## 4. Build Market Factor Features

```bash
python scripts/build_features.py
```

## 5. Run TimesFM Rolling Backtest

```bash
python scripts/backtest_timesfm.py
```

## 6. Merge TimesFM Forecasts into ML Features

```bash
python scripts/merge_timesfm_features.py
```

## 7. Train and Compare Models

```bash
python scripts/train_factor_timesfm_model.py
```

## 8. Build GitHub Pages Site

```bash
python scripts/build_site.py
```

---

## GitHub Actions and GitHub Pages

The project includes a GitHub Actions workflow that can run the ETL pipeline and deploy a static dashboard to GitHub Pages.

Workflow file:

```text
.github/workflows/etl.yml
```

GitHub Pages dashboard:

```text
https://jesstank.github.io/etl_stocks/
```

---

## Final Model Results

The final comparison table is stored in:

```text
reports/factor_timesfm_model_results.csv
```

The main comparison charts are stored in:

```text
reports/figures/factor_timesfm_model_comparison_mae.png
reports/figures/factor_timesfm_model_comparison_direction.png
reports/figures/factor_timesfm_feature_importance.png
```

---

## Key Takeaways

1. A complete ETL pipeline was built for energy stock market data.
2. Market factors such as WTI, SPY, XLE, VIX, volume, moving-average distance, and volatility were engineered.
3. TimesFM was tested as a zero-shot univariate forecasting model.
4. TimesFM rolling forecasts were converted into ML features.
5. Factor-only tree models showed the best directional accuracy in the current test window.
6. TimesFM features did not improve model performance in the current setup.
7. Short-term next-day stock return forecasting remains highly noisy and difficult.
8. Honest baseline comparison is essential for financial forecasting projects.

---

# 中文说明

## 项目概述

**ETL_STOCKS** 是一个能源股票 ETL、预测和模型比较项目。项目使用 Python 自动抓取能源股票和市场因子数据，清洗后存入 SQLite 数据库，并结合 Google Research 的 TimesFM 模型和传统机器学习模型进行预测实验。

本项目的重点不是声称可以准确预测股价，而是展示一个完整、真实、可复现的金融数据工程和建模流程。

---

## 项目流程

```text
抓取股票数据
        ↓
清洗数据
        ↓
写入 SQLite
        ↓
构建市场因子
        ↓
运行 TimesFM rolling backtest
        ↓
将 TimesFM 预测结果转成 ML feature
        ↓
比较 factor-only、TimesFM-only、factor+TimesFM 模型
        ↓
通过 GitHub Pages 展示结果
```

---

## 当前结论

当前模型结果显示：

```text
factor-only 的 Random Forest 和 Gradient Boosting 方向预测表现最好
TimesFM-only 模型没有稳定超过 baseline
factor + TimesFM 没有比 factor-only 更好
zero-return baseline 在 MAE 上仍然很强
```

这说明短期 next-day stock return 非常 noisy，仅靠当前这些特征很难稳定预测。

这个结果本身是有价值的，因为项目没有硬吹模型，而是通过 baseline、backtest 和 model comparison 做了真实评估。

---

## 项目亮点

```text
Python ETL
SQLite database
Financial feature engineering
TimesFM rolling backtest
Market factor modeling
Model comparison
GitHub Actions
GitHub Pages dashboard
Honest baseline evaluation
```

---

## Disclaimer

This project is for educational and portfolio purposes only. It is not financial advice and should not be used as a trading system.
