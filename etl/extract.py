"""
ETL Pipeline — Extract module
Reads raw CSV files from data/raw/ directory.
"""

import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def extract_all() -> dict[str, pd.DataFrame]:
    """Extract all CSV files and return as a dict of DataFrames."""
    tables = ["agents", "campaigns", "leads", "calls", "sales"]
    dfs = {}
    for table in tables:
        path = os.path.join(RAW_DIR, f"{table}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌  Missing file: {path}")
        dfs[table] = pd.read_csv(path)
        logger.info(f"  Extracted {table}: {len(dfs[table]):,} rows")
    return dfs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = extract_all()
    for name, df in data.items():
        print(f"{name:12s}: {len(df):>6,} rows | columns: {list(df.columns)}")
