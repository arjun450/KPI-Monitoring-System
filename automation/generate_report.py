"""
Automation — Report Generator
Generates a daily business insights PDF/HTML report.
"""

import os
import sys
import pandas as pd
import sqlalchemy as sa
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))
from load import get_engine

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def fetch_report_data(engine) -> dict:
    with engine.connect() as conn:
        kpi_summary = pd.read_sql(sa.text("""
            SELECT
                COUNT(*) AS total_calls,
                SUM(is_connected) AS connected_calls,
                ROUND(100.0 * SUM(is_connected) / MAX(COUNT(*), 1), 2) AS connection_rate
            FROM calls
        """), conn)

        campaign_perf = pd.read_sql(sa.text("""
            SELECT
                c.campaign_name,
                COUNT(s.sale_id)       AS total_sales,
                ROUND(SUM(s.revenue),2) AS revenue,
                ROUND(AVG(s.acquisition_cost),2) AS avg_cac
            FROM sales s
            JOIN campaigns c ON s.campaign_id = c.campaign_id
            GROUP BY c.campaign_name
            ORDER BY revenue DESC
            LIMIT 10
        """), conn)

        agent_perf = pd.read_sql(sa.text("""
            SELECT
                a.agent_name, a.team,
                COUNT(DISTINCT c.call_id) AS calls
            FROM agents a
            JOIN calls c ON a.agent_id = c.agent_id
            GROUP BY a.agent_name, a.team
            ORDER BY calls DESC
            LIMIT 10
        """), conn)

        monthly_rev = pd.read_sql(sa.text("""
            SELECT sale_month, ROUND(SUM(revenue),2) AS revenue, COUNT(*) AS sales
            FROM sales
            GROUP BY sale_month
            ORDER BY sale_month
        """), conn)

        segment_rev = pd.read_sql(sa.text("""
            SELECT l.customer_segment,
                   COUNT(s.sale_id) AS total_sales,
                   ROUND(SUM(s.revenue),2) AS revenue
            FROM sales s
            JOIN leads l ON s.lead_id = l.lead_id
            GROUP BY l.customer_segment
            ORDER BY revenue DESC
        """), conn)

        alerts = pd.read_sql(sa.text("""
            SELECT alert_time, metric_name, actual_val, target_val, severity, message
            FROM kpi_alerts
            ORDER BY alert_time DESC
            LIMIT 20
        """), conn)

    return {
        "campaign_perf": campaign_perf,
        "agent_perf":    agent_perf,
        "monthly_rev":   monthly_rev,
        "segment_rev":   segment_rev,
        "alerts":        alerts,
    }


def generate_html_report(data: dict) -> str:
    """Generate an HTML report from the report data."""
    today = datetime.now().strftime("%B %d, %Y")
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")

    def df_to_html(df, style=""):
        return df.to_html(index=False, border=0, classes="table", justify="left")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Business KPI Daily Report — {today}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1e293b; background: #f8fafc; }}
  h1   {{ color: #1e3a5f; border-bottom: 3px solid #3985D6; padding-bottom: 10px; }}
  h2   {{ color: #3985D6; margin-top: 30px; }}
  .table {{ width:100%; border-collapse:collapse; margin-top:10px; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,0.1); }}
  .table th {{ background:#3985D6; color:#fff; padding:10px 14px; text-align:left; }}
  .table td {{ padding:9px 14px; border-bottom:1px solid #e2e8f0; }}
  .table tr:hover td {{ background:#f1f5f9; }}
  .alert-warning  {{ background:#fefce8; border-left:4px solid #ca8a04; padding:8px 14px; margin:4px 0; border-radius:0 6px 6px 0; }}
  .alert-critical {{ background:#fef2f2; border-left:4px solid #dc2626; padding:8px 14px; margin:4px 0; border-radius:0 6px 6px 0; }}
  .footer {{ color:#94a3b8; font-size:12px; margin-top:40px; border-top:1px solid #e2e8f0; padding-top:12px; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:20px 0; }}
  .kpi-card {{ background:#fff; border-radius:10px; padding:18px; box-shadow:0 1px 4px rgba(0,0,0,0.1); text-align:center; }}
  .kpi-card .value {{ font-size:28px; font-weight:700; color:#3985D6; }}
  .kpi-card .label {{ font-size:13px; color:#64748b; margin-top:4px; }}
</style>
</head>
<body>
<h1>📊 Automated Business KPI Report</h1>
<p><strong>Generated:</strong> {today} &nbsp;|&nbsp; <strong>System:</strong> KPI Monitoring System v1.0</p>

<h2>📈 Campaign Performance</h2>
{df_to_html(data["campaign_perf"])}

<h2>👤 Top Agents by Call Volume</h2>
{df_to_html(data["agent_perf"])}

<h2>📅 Monthly Revenue Trend</h2>
{df_to_html(data["monthly_rev"])}

<h2>🏷️ Revenue by Customer Segment</h2>
{df_to_html(data["segment_rev"])}

<h2>⚠️ Recent Alerts</h2>
"""
    if data["alerts"].empty:
        html += "<p style='color:green'>✅ No active alerts.</p>"
    else:
        for _, row in data["alerts"].iterrows():
            cls = "alert-critical" if row["severity"] == "CRITICAL" else "alert-warning"
            html += f'<div class="{cls}"><strong>[{row["severity"]}]</strong> {row["message"]}</div>\n'

    html += f"""
<div class="footer">
  <p>This report is auto-generated by the KPI Monitoring System. Do not reply to this message.</p>
  <p>Report ID: {ts}</p>
</div>
</body>
</html>"""
    return html


def generate_report():
    engine = get_engine()
    data   = fetch_report_data(engine)
    html   = generate_html_report(data)

    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = os.path.join(REPORTS_DIR, f"kpi_report_{ts}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅  Report saved: {out_path}")
    return out_path


if __name__ == "__main__":
    path = generate_report()
    print(f"Open in browser: file:///{path.replace(os.sep, '/')}")
