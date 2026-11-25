"""
ETL Pipeline — Load module
Loads cleaned, transformed data into SQLite (portable, no server needed).
Falls back to PostgreSQL if DATABASE_URL env var is set.
"""

import os
import logging
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "kpi_monitoring.db")

def get_engine():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        logger.info(f"Connecting to PostgreSQL: {db_url.split('@')[-1]}")
        return sa.create_engine(db_url)
    else:
        logger.info(f"Using SQLite: {DB_PATH}")
        return sa.create_engine(f"sqlite:///{DB_PATH}")


def create_schema(engine):
    """Create tables if they don't exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS agents (
        agent_id    INTEGER PRIMARY KEY,
        agent_name  TEXT NOT NULL,
        team        TEXT,
        joining_date TEXT,
        manager_id  INTEGER
    );
    CREATE TABLE IF NOT EXISTS campaigns (
        campaign_id   INTEGER PRIMARY KEY,
        campaign_name TEXT NOT NULL,
        budget        REAL,
        start_date    TEXT,
        end_date      TEXT,
        target_leads  INTEGER
    );
    CREATE TABLE IF NOT EXISTS leads (
        lead_id          INTEGER PRIMARY KEY,
        customer_segment TEXT,
        campaign_id      INTEGER,
        lead_created_at  TEXT,
        lead_source      TEXT,
        city             TEXT,
        lead_date        TEXT,
        lead_month       TEXT
    );
    CREATE TABLE IF NOT EXISTS calls (
        call_id        INTEGER PRIMARY KEY,
        lead_id        INTEGER,
        agent_id       INTEGER,
        call_timestamp TEXT,
        call_duration  INTEGER,
        call_status    TEXT,
        call_outcome   TEXT,
        call_hour      INTEGER,
        call_date      TEXT,
        call_weekday   TEXT,
        call_month     TEXT,
        is_connected   INTEGER,
        is_converted   INTEGER
    );
    CREATE TABLE IF NOT EXISTS sales (
        sale_id          INTEGER PRIMARY KEY,
        lead_id          INTEGER,
        campaign_id      INTEGER,
        sale_date        TEXT,
        revenue          REAL,
        acquisition_cost REAL,
        sale_month       TEXT,
        profit_margin    REAL
    );
    CREATE TABLE IF NOT EXISTS kpi_alerts (
        alert_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_time  TEXT DEFAULT (datetime('now')),
        metric_name TEXT,
        actual_val  REAL,
        target_val  REAL,
        deviation   REAL,
        severity    TEXT,
        message     TEXT,
        resolved    INTEGER DEFAULT 0
    );
    """
    with engine.connect() as conn:
        for stmt in ddl.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
    logger.info("✅  Schema created / verified")


def load_table(df: pd.DataFrame, table: str, engine, if_exists="replace"):
    """Load a DataFrame into a database table."""
    # Convert datetime columns to strings for SQLite compatibility
    df = df.copy()
    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]):
        df[col] = df[col].astype(str)
    df.to_sql(table, engine, if_exists=if_exists, index=False, chunksize=5000)
    logger.info(f"  Loaded {len(df):>6,} rows → {table}")


def load_all(dfs: dict, engine=None, if_exists="replace"):
    """Load all tables into the database."""
    if engine is None:
        engine = get_engine()
    create_schema(engine)
    for table_name, df in dfs.items():
        load_table(df, table_name, engine, if_exists=if_exists)
    logger.info("✅  All tables loaded")
    return engine


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from extract   import extract_all
    from validate  import validate_all
    from transform import transform_all

    raw       = extract_all()
    cleaned   = validate_all(raw)
    final     = transform_all(cleaned)
    engine    = load_all(final)
    print("\n✅  ETL complete. Database ready.")
