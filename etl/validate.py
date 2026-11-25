"""
ETL Pipeline — Validate module
Checks data quality and referential integrity before loading.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


def _check(condition: bool, msg: str):
    if not condition:
        raise ValidationError(msg)


def validate_agents(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Validating agents...")
    df = df.drop_duplicates(subset=["agent_id"])
    _check(df["agent_id"].notna().all(),   "agents: null agent_id found")
    _check(df["agent_name"].notna().all(), "agents: null agent_name found")
    df["joining_date"] = pd.to_datetime(df["joining_date"], errors="coerce")
    return df


def validate_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Validating campaigns...")
    df = df.drop_duplicates(subset=["campaign_id"])
    _check(df["campaign_id"].notna().all(), "campaigns: null campaign_id")
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"]   = pd.to_datetime(df["end_date"],   errors="coerce")
    df["budget"]     = pd.to_numeric(df["budget"], errors="coerce").fillna(0)
    return df


def validate_leads(df: pd.DataFrame, campaign_ids: set) -> pd.DataFrame:
    logger.info("Validating leads...")
    df = df.drop_duplicates(subset=["lead_id"])
    _check(df["lead_id"].notna().all(), "leads: null lead_id")
    df["lead_created_at"] = pd.to_datetime(df["lead_created_at"], errors="coerce")
    # Drop rows with unparseable timestamps
    invalid_ts = df["lead_created_at"].isna()
    if invalid_ts.sum() > 0:
        logger.warning(f"  Dropping {invalid_ts.sum()} leads with invalid timestamps")
        df = df[~invalid_ts]
    # Remove orphaned campaign references
    orphans = ~df["campaign_id"].isin(campaign_ids)
    if orphans.sum() > 0:
        logger.warning(f"  Dropping {orphans.sum()} leads with invalid campaign_id")
        df = df[~orphans]
    return df


def validate_calls(df: pd.DataFrame, lead_ids: set, agent_ids: set) -> pd.DataFrame:
    logger.info("Validating calls...")
    df = df.drop_duplicates(subset=["call_id"])
    df["call_timestamp"] = pd.to_datetime(df["call_timestamp"], errors="coerce")
    df = df.dropna(subset=["call_id", "lead_id", "call_timestamp"])
    # Remove negative durations
    before = len(df)
    df = df[df["call_duration"] >= 0]
    logger.info(f"  Removed {before - len(df)} rows with negative call duration")
    # Referential integrity
    df = df[df["lead_id"].isin(lead_ids) & df["agent_id"].isin(agent_ids)]
    return df


def validate_sales(df: pd.DataFrame, lead_ids: set, campaign_ids: set) -> pd.DataFrame:
    logger.info("Validating sales...")
    df = df.drop_duplicates(subset=["sale_id"])
    df["sale_date"]        = pd.to_datetime(df["sale_date"], errors="coerce")
    df["revenue"]          = pd.to_numeric(df["revenue"],          errors="coerce").fillna(0)
    df["acquisition_cost"] = pd.to_numeric(df["acquisition_cost"], errors="coerce").fillna(0)
    df = df[df["lead_id"].isin(lead_ids)]
    return df


def validate_all(dfs: dict) -> dict:
    """Run all validations and return cleaned DataFrames."""
    agents    = validate_agents(dfs["agents"])
    campaigns = validate_campaigns(dfs["campaigns"])
    leads     = validate_leads(dfs["leads"], set(campaigns["campaign_id"]))
    calls     = validate_calls(dfs["calls"], set(leads["lead_id"]), set(agents["agent_id"]))
    sales     = validate_sales(dfs["sales"], set(leads["lead_id"]), set(campaigns["campaign_id"]))

    cleaned = {
        "agents": agents, "campaigns": campaigns,
        "leads": leads, "calls": calls, "sales": sales
    }
    for name, df in cleaned.items():
        logger.info(f"  ✅ {name:12s}: {len(df):>6,} rows after validation")
    return cleaned


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from extract import extract_all
    raw  = extract_all()
    clean = validate_all(raw)
