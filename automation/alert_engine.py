"""
Automation — Alert Engine
Fetches current KPI values and compares against thresholds.
Logs alerts to database and optionally sends email notifications.
"""

import os
import sys
import logging
import yaml
import pandas as pd
import sqlalchemy as sa
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))
from load import get_engine

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "thresholds.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def fetch_kpis(engine) -> dict:
    """Calculate current KPI snapshot from the database."""
    q = {
        "total_calls": "SELECT COUNT(*) FROM calls",
        "connected_calls": "SELECT COUNT(*) FROM calls WHERE call_status='Connected'",
        "total_leads": "SELECT COUNT(*) FROM leads",
        "total_sales": "SELECT COUNT(*) FROM sales",
        "total_revenue": "SELECT COALESCE(SUM(revenue),0) FROM sales",
        "total_cac": "SELECT COALESCE(SUM(acquisition_cost),0) FROM sales",
    }
    vals = {}
    with engine.connect() as conn:
        for key, sql in q.items():
            vals[key] = conn.execute(sa.text(sql)).scalar()

    # Compute derived KPIs
    total_calls    = vals["total_calls"] or 1
    connected      = vals["connected_calls"] or 0
    total_leads    = vals["total_leads"] or 1
    total_sales    = vals["total_sales"] or 0
    total_revenue  = vals["total_revenue"] or 0
    total_cac      = vals["total_cac"] or 1

    kpis = {
        "connection_rate_pct":  round(100.0 * connected / total_calls, 2),
        "conversion_rate_pct":  round(100.0 * total_sales / total_leads, 2),
        "avg_cac":              round(total_cac / max(total_sales, 1), 2),
        "roas":                 round(total_revenue / max(total_cac, 1), 2),
    }

    # Month-over-month revenue drop
    with engine.connect() as conn:
        monthly = pd.read_sql(
            sa.text("""
                SELECT substr(sale_date,1,7) AS month, SUM(revenue) AS rev
                FROM sales
                GROUP BY substr(sale_date,1,7)
                ORDER BY month DESC
                LIMIT 2
            """), conn
        )
    if len(monthly) == 2:
        curr, prev = monthly.iloc[0]["rev"], monthly.iloc[1]["rev"]
        kpis["revenue_drop_pct"] = round(100.0 * (prev - curr) / max(prev, 1), 2) if curr < prev else 0
    else:
        kpis["revenue_drop_pct"] = 0

    return kpis


def evaluate_alerts(kpis: dict, config: dict) -> list[dict]:
    """Compare KPI values against thresholds and produce alert records."""
    alerts = []
    thresholds = config.get("kpis", {})

    for metric, kpi_cfg in thresholds.items():
        if metric not in kpis:
            continue

        actual    = kpis[metric]
        direction = kpi_cfg.get("direction", "below")
        warn_lvl  = kpi_cfg.get("warning")
        crit_lvl  = kpi_cfg.get("critical")

        def triggered(actual, threshold):
            if direction == "above":
                return actual > threshold
            return actual < threshold

        severity = None
        if crit_lvl is not None and triggered(actual, crit_lvl):
            severity  = "CRITICAL"
            threshold = crit_lvl
        elif warn_lvl is not None and triggered(actual, warn_lvl):
            severity  = "WARNING"
            threshold = warn_lvl

        if severity:
            deviation = round(actual - threshold, 4)
            msg = (
                f"{severity}: {metric} = {actual} {kpi_cfg.get('unit','')}  "
                f"(threshold: {threshold} {kpi_cfg.get('unit','')}, "
                f"deviation: {deviation:+})"
            )
            logger.warning(msg)
            alerts.append({
                "alert_time":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "metric_name": metric,
                "actual_val":  actual,
                "target_val":  threshold,
                "deviation":   deviation,
                "severity":    severity,
                "message":     msg,
                "resolved":    0,
            })

    return alerts


def save_alerts(alerts: list[dict], engine):
    if not alerts:
        logger.info("✅  No alerts triggered.")
        return
    df = pd.DataFrame(alerts)
    df.to_sql("kpi_alerts", engine, if_exists="append", index=False)
    logger.info(f"⚠️  {len(df)} alert(s) saved to database.")


def run_alert_check():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    logger.info("=" * 55)
    logger.info("KPI Alert Engine — %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("=" * 55)

    engine  = get_engine()
    config  = load_config()
    kpis    = fetch_kpis(engine)

    logger.info("Current KPI snapshot:")
    for k, v in kpis.items():
        logger.info(f"  {k:<30s}: {v}")

    alerts = evaluate_alerts(kpis, config)
    save_alerts(alerts, engine)
    return alerts


if __name__ == "__main__":
    alerts = run_alert_check()
    if alerts:
        print(f"\n⚠️  {len(alerts)} alert(s) triggered!")
        for a in alerts:
            print(f"  [{a['severity']}] {a['message']}")
    else:
        print("\n✅  All KPIs within acceptable ranges.")
