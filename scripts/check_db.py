from pathlib import Path
import sqlite3
import pandas as pd


# Make pandas output easier to read in terminal
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)


# Find project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "etl_stocks.db"


def check_database_exists():
    print("Checking database file...")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    print(f"Database found: {DB_PATH}")


def show_tables(conn):
    print("\nTables in database:")

    query = """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table';
    """

    tables = pd.read_sql_query(query, conn)
    print(tables)


def show_table_schema(conn):
    print("\nSchema for stock_prices:")

    query = """
    PRAGMA table_info(stock_prices);
    """

    schema = pd.read_sql_query(query, conn)
    print(schema)


def show_sample_rows(conn):
    print("\nFirst 10 rows:")

    query = """
    SELECT *
    FROM stock_prices
    LIMIT 10;
    """

    sample = pd.read_sql_query(query, conn)
    print(sample)


def show_summary_by_ticker(conn):
    print("\nSummary by ticker:")

    query = """
    SELECT
        ticker,
        COUNT(*) AS row_count,
        MIN(Date) AS start_date,
        MAX(Date) AS end_date,
        ROUND(AVG(daily_return), 6) AS avg_daily_return,
        ROUND(MIN(Close), 2) AS min_close,
        ROUND(MAX(Close), 2) AS max_close,
        ROUND(AVG(Volume), 0) AS avg_volume
    FROM stock_prices
    GROUP BY ticker
    ORDER BY ticker;
    """

    summary = pd.read_sql_query(query, conn)
    print(summary)


def show_latest_prices(conn):
    print("\nLatest 5 prices for each ticker:")

    query = """
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY ticker
                ORDER BY Date DESC
            ) AS row_num
        FROM stock_prices
    )
    WHERE row_num <= 5
    ORDER BY ticker, Date DESC;
    """

    latest = pd.read_sql_query(query, conn)
    print(latest)


def main():
    check_database_exists()

    conn = sqlite3.connect(DB_PATH)

    show_tables(conn)
    show_table_schema(conn)
    show_sample_rows(conn)
    show_summary_by_ticker(conn)
    show_latest_prices(conn)

    conn.close()

    print("\nDatabase check completed successfully.")


if __name__ == "__main__":
    main()