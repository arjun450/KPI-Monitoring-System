"""
ETL Pipeline — Transform module
Applies business logic transformations before loading.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def transform_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to calls."""
    df = df.copy()
    df["call_date"]      = df["call_timestamp"].dt.date
    df["call_hour"]      = df["call_timestamp"].dt.hour
    df["call_weekday"]   = df["call_timestamp"].dt.day_name()
    df["call_month"]     = df["call_timestamp"].dt.to_period("M").astype(str)
    df["is_connected"]   = (df["call_status"] == "Connected").astype(int)
    df["is_converted"]   = (df["call_outcome"] == "Converted").astype(int)
    return df


def transform_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to leads."""
    df = df.copy()
    df["lead_date"]  = df["lead_created_at"].dt.date
    df["lead_month"] = df["lead_created_at"].dt.to_period("M").astype(str)
    return df


def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to sales."""
    df = df.copy()
    df["sale_month"]     = pd.to_datetime(df["sale_date"]).dt.to_period("M").astype(str)
    df["profit_margin"]  = df["revenue"] - df["acquisition_cost"]
    return df


def transform_all(dfs: dict) -> dict:
    """Apply all transformations."""
    transformed = {
        "agents":    dfs["agents"].copy(),
        "campaigns": dfs["campaigns"].copy(),
        "leads":     transform_leads(dfs["leads"]),
        "calls":     transform_calls(dfs["calls"]),
        "sales":     transform_sales(dfs["sales"]),
    }
    logger.info("✅  All transformations applied")
    return transformed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from extract  import extract_all
    from validate import validate_all
    raw       = extract_all()
    cleaned   = validate_all(raw)
    final     = transform_all(cleaned)
    print(final["calls"].head(3))
