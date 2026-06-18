# ETL_STOCKS: Energy Stock Market ETL Pipeline

## English Version

## Project Overview

**ETL_STOCKS** is a Python-based ETL pipeline designed to collect, clean, store, and analyze historical energy stock market data. The project extracts stock price data for major energy companies, transforms raw market data into analysis-ready datasets, loads the processed data into a SQLite database, and generates summary reports and visualizations for financial analysis.

This project demonstrates a complete end-to-end data workflow, including data extraction, data transformation, database loading, SQL validation, and automated report generation.

---

## Business Objective

Energy companies are strongly affected by market volatility, commodity prices, investor sentiment, and macroeconomic conditions. This project focuses on analyzing the historical performance of selected energy stocks and answering questions such as:

* How have major energy stocks performed over time?
* Which stock had the highest total return during the selected period?
* Which stock showed the highest volatility?
* How do normalized stock prices compare across companies?
* What does the daily return distribution reveal about risk?

The goal is to build a lightweight but professional ETL pipeline that converts raw financial data into structured insights.

---

## Stocks Analyzed

The current version analyzes the following major energy companies:

| Ticker | Company                          |
| ------ | -------------------------------- |
| XOM    | Exxon Mobil Corporation          |
| CVX    | Chevron Corporation              |
| OXY    | Occidental Petroleum Corporation |

---

## Tech Stack

* **Python** — main programming language
* **Pandas** — data cleaning, transformation, and analysis
* **yfinance** — stock market data extraction
* **SQLite** — lightweight relational database
* **Matplotlib** — data visualization
* **VS Code** — development environment
* **Conda** — Python environment management

---

## ETL Pipeline Design

### 1. Extract

The pipeline extracts historical stock data from Yahoo Finance using the `yfinance` package.

Extracted fields include:

* Date
* Open price
* High price
* Low price
* Close price
* Adjusted close price
* Trading volume
* Stock ticker

Raw data is saved into the `data/raw/` folder.

---

### 2. Transform

The transformation step cleans and prepares the data for analysis.

Main transformation tasks include:

* Standardizing date format
* Sorting records by ticker and date
* Converting numeric columns
* Removing missing values
* Calculating daily return
* Calculating 7-day moving average
* Calculating 30-day moving average

The cleaned dataset is saved into:

```text
data/processed/stock_prices_processed.csv
```

---

### 3. Load

The processed dataset is loaded into a SQLite database:

```text
data/etl_stocks.db
```

The main database table is:

```text
stock_prices
```

This allows the data to be queried using SQL and reused for further analysis.

---

## Project Structure

```text
ETL_STOCKS/
│
├── data/
│   ├── raw/
│   │   ├── XOM_raw.csv
│   │   ├── CVX_raw.csv
│   │   └── OXY_raw.csv
│   │
│   ├── processed/
│   │   └── stock_prices_processed.csv
│   │
│   └── etl_stocks.db
│
├── reports/
│   ├── ticker_summary.csv
│   │
│   └── figures/
│       ├── close_price_trend.png
│       ├── normalized_price_trend.png
│       └── daily_return_distribution.png
│
├── scripts/
│   ├── main.py
│   ├── check_db.py
│   └── analyze_db.py
│
├── requirements.txt
└── README.md
```

---

## How to Run the Project

### 1. Activate the Conda Environment

```bash
conda activate etl-env
```

### 2. Install Required Packages

```bash
pip install -r requirements.txt
```

### 3. Run the ETL Pipeline

```bash
python scripts/main.py
```

This will extract raw stock data, transform it, and load the processed dataset into SQLite.

### 4. Validate the Database

```bash
python scripts/check_db.py
```

This script checks whether the SQLite database exists, lists available tables, prints the table schema, and displays sample rows.

### 5. Generate Analysis Reports and Visualizations

```bash
python scripts/analyze_db.py
```

This will generate summary reports and charts under the `reports/` folder.

---

## Output Files

### Processed Dataset

```text
data/processed/stock_prices_processed.csv
```

### SQLite Database

```text
data/etl_stocks.db
```

### Summary Report

```text
reports/ticker_summary.csv
```

### Visualizations

```text
reports/figures/close_price_trend.png
reports/figures/normalized_price_trend.png
reports/figures/daily_return_distribution.png
```

---

## Analysis Features

The project generates the following analytical outputs:

### Stock Performance Summary

The summary report includes:

* Row count
* Start date
* End date
* Starting close price
* Ending close price
* Minimum close price
* Maximum close price
* Average daily return
* Volatility
* Average trading volume
* Total return

### Close Price Trend

This chart shows the historical close price trend of each stock.

### Normalized Price Trend

This chart normalizes each stock’s starting price to 100, allowing a fair comparison of relative performance.

### Daily Return Distribution

This chart shows the distribution of daily returns, which helps compare volatility and risk across stocks.

---

## What This Project Demonstrates

This project demonstrates practical data engineering and analytics skills, including:

* Building an end-to-end ETL pipeline
* Extracting data from financial APIs
* Cleaning and transforming time-series data
* Loading structured data into a relational database
* Validating database tables with SQL
* Creating reusable Python scripts
* Generating automated analytical reports
* Producing visualizations for financial interpretation
* Organizing a data project using a professional folder structure

---

## Future Improvements

Potential future upgrades include:

* Add WTI crude oil price data
* Analyze correlation between crude oil prices and energy stocks
* Add GitHub Actions for scheduled automatic ETL runs
* Add data quality checks
* Store results in PostgreSQL
* Build an interactive dashboard with Streamlit or Tableau
* Add unit tests for ETL functions
* Add logging and error handling
* Deploy the pipeline as a scheduled cloud workflow

---

## Resume Description

**Energy Stock Market ETL Pipeline**

Built an end-to-end ETL pipeline using Python, Pandas, yfinance, and SQLite to extract, clean, store, and analyze historical energy stock market data. Created reusable scripts for data extraction, transformation, database validation, and report generation. Produced summary reports and visualizations to compare stock performance, daily returns, volatility, and normalized price trends across major energy companies.

---

# 中文版本

## 项目概述

**ETL_STOCKS** 是一个基于 Python 的能源股票市场 ETL 项目。该项目可以自动抓取主要能源公司的历史股票数据，对原始数据进行清洗和转换，并将处理后的数据加载到 SQLite 数据库中，最后生成分析报告和可视化图表。

这个项目展示了一个完整的数据分析工作流：

```text
数据提取 → 数据清洗 → 数据转换 → 数据库存储 → SQL 验证 → 报告和图表生成
```

它不是一个简单的 Notebook，而是一个结构完整、可以复现、可以扩展的 ETL Pipeline 项目。

---

## 项目目标

能源公司的股票价格会受到油价、宏观经济、市场情绪和行业周期的影响。本项目通过分析能源股票的历史价格数据，尝试回答以下问题：

* 主要能源股票的历史走势如何？
* 哪只股票在分析期间表现最好？
* 哪只股票波动最大？
* 如果把起点都设为 100，不同股票的相对表现如何？
* 每日收益率分布能反映出什么风险特征？

项目目标是将原始金融数据转换成结构化、可查询、可分析的数据资产。

---

## 当前分析股票

| Ticker | 公司                               |
| ------ | -------------------------------- |
| XOM    | Exxon Mobil Corporation          |
| CVX    | Chevron Corporation              |
| OXY    | Occidental Petroleum Corporation |

---

## 技术栈

* **Python**：主要开发语言
* **Pandas**：数据清洗、转换和分析
* **yfinance**：获取股票市场数据
* **SQLite**：轻量级关系型数据库
* **Matplotlib**：数据可视化
* **VS Code**：代码开发环境
* **Conda**：Python 环境管理

---

## ETL 流程设计

### 1. Extract：数据提取

项目使用 `yfinance` 从 Yahoo Finance 抓取历史股票数据。

抓取字段包括：

* 日期
* 开盘价
* 最高价
* 最低价
* 收盘价
* 复权收盘价
* 成交量
* 股票代码

原始数据会保存到：

```text
data/raw/
```

---

### 2. Transform：数据转换

转换阶段会将原始股票数据清洗成适合分析的格式。

主要处理步骤包括：

* 标准化日期格式
* 按股票代码和日期排序
* 转换数值字段
* 删除缺失值
* 计算每日收益率
* 计算 7 日移动平均线
* 计算 30 日移动平均线

处理后的数据会保存到：

```text
data/processed/stock_prices_processed.csv
```

---

### 3. Load：数据加载

清洗后的数据会被加载到 SQLite 数据库：

```text
data/etl_stocks.db
```

核心数据表为：

```text
stock_prices
```

这样数据就可以通过 SQL 查询，并支持后续分析和报表生成。

---

## 项目结构

```text
ETL_STOCKS/
│
├── data/
│   ├── raw/
│   │   ├── XOM_raw.csv
│   │   ├── CVX_raw.csv
│   │   └── OXY_raw.csv
│   │
│   ├── processed/
│   │   └── stock_prices_processed.csv
│   │
│   └── etl_stocks.db
│
├── reports/
│   ├── ticker_summary.csv
│   │
│   └── figures/
│       ├── close_price_trend.png
│       ├── normalized_price_trend.png
│       └── daily_return_distribution.png
│
├── scripts/
│   ├── main.py
│   ├── check_db.py
│   └── analyze_db.py
│
├── requirements.txt
└── README.md
```

---

## 如何运行项目

### 1. 激活 Conda 环境

```bash
conda activate etl-env
```

### 2. 安装依赖包

```bash
pip install -r requirements.txt
```

### 3. 运行 ETL Pipeline

```bash
python scripts/main.py
```

该脚本会完成数据提取、数据转换和数据库加载。

### 4. 检查 SQLite 数据库

```bash
python scripts/check_db.py
```

该脚本会检查数据库文件是否存在、数据库中有哪些表、表结构是否正确，以及数据是否成功写入。

### 5. 生成分析报告和图表

```bash
python scripts/analyze_db.py
```

该脚本会在 `reports/` 文件夹中生成 summary report 和图表。

---

## 输出结果

### 处理后的数据

```text
data/processed/stock_prices_processed.csv
```

### SQLite 数据库

```text
data/etl_stocks.db
```

### 汇总报告

```text
reports/ticker_summary.csv
```

### 可视化图表

```text
reports/figures/close_price_trend.png
reports/figures/normalized_price_trend.png
reports/figures/daily_return_distribution.png
```

---

## 分析内容

项目会自动生成以下分析结果：

### 股票表现汇总

汇总报告包括：

* 数据行数
* 起始日期
* 结束日期
* 起始收盘价
* 结束收盘价
* 最低收盘价
* 最高收盘价
* 平均每日收益率
* 波动率
* 平均成交量
* 总收益率

### 收盘价趋势图

展示每只股票的历史收盘价走势。

### 标准化价格趋势图

将每只股票的起点都标准化为 100，用于公平比较不同股票的相对表现。

### 每日收益率分布图

展示不同股票每日收益率的分布情况，用于比较波动性和风险。

---

## 项目展示能力

这个项目展示了以下数据分析和数据工程能力：

* 构建端到端 ETL Pipeline
* 使用 API 抽取金融市场数据
* 清洗和转换时间序列数据
* 将结构化数据加载到关系型数据库
* 使用 SQL 验证数据库内容
* 编写可复用的 Python 脚本
* 自动生成分析报告
* 使用图表解释金融数据
* 按照专业项目结构组织代码和数据

---

## 后续改进方向

后续可以继续升级：

* 加入 WTI 原油价格数据
* 分析原油价格与能源股票之间的相关性
* 使用 GitHub Actions 实现定时自动运行
* 添加数据质量检查
* 将 SQLite 升级为 PostgreSQL
* 使用 Streamlit 或 Tableau 制作交互式 Dashboard
* 为 ETL 函数添加单元测试
* 添加日志和错误处理
* 将 Pipeline 部署为云端定时任务

---

## 简历描述

**能源股票市场 ETL Pipeline 项目**

使用 Python、Pandas、yfinance 和 SQLite 构建了一个端到端 ETL Pipeline，用于自动抓取、清洗、存储和分析能源股票历史市场数据。项目包含数据提取、数据转换、数据库加载、SQL 验证、报告生成和数据可视化模块，并通过 summary report 和图表比较了主要能源公司的股票表现、每日收益率、波动率和标准化价格走势。
