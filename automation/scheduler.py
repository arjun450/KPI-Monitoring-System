"""
Automation — Scheduler
Runs the full pipeline: ETL → Alert Check → Report Generation.
Can be run once manually or set up with Windows Task Scheduler / cron.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Add parent directories to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "etl"))
sys.path.insert(0, os.path.join(BASE_DIR, "automation"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, "reports", "pipeline.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=" * 60)
    logger.info("🚀  KPI Monitoring Pipeline — %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    # Step 1: ETL
    logger.info("Step 1/3  Running ETL pipeline...")
    from extract   import extract_all
    from validate  import validate_all
    from transform import transform_all
    from load      import load_all, get_engine

    raw     = extract_all()
    cleaned = validate_all(raw)
    final   = transform_all(cleaned)
    engine  = load_all(final)
    logger.info("Step 1/3  ✅ ETL complete")

    # Step 2: Alert Check
    logger.info("Step 2/3  Running KPI alert check...")
    from alert_engine import run_alert_check
    alerts = run_alert_check()
    logger.info(f"Step 2/3  ✅ Alert check complete — {len(alerts)} alert(s)")

    # Step 3: Generate Report
    logger.info("Step 3/3  Generating daily report...")
    from generate_report import generate_report
    report_path = generate_report()
    logger.info("Step 3/3  ✅ Report generated: %s", report_path)

    logger.info("=" * 60)
    logger.info("✅  Pipeline finished successfully")
    logger.info("=" * 60)
    return {"alerts": alerts, "report": report_path}


if __name__ == "__main__":
    result = run_pipeline()
    print(f"\n📄 Report: {result['report']}")
    if result["alerts"]:
        print(f"⚠️  {len(result['alerts'])} KPI alert(s) logged — check the dashboard.")
