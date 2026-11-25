"""
KPI Monitoring System — Interactive Dashboard
Built with Streamlit. Run with: streamlit run dashboard/app.py

Provides four pages matching the Power BI design spec:
  1. Executive Overview
  2. Sales & Campaign Analysis
  3. Operational Performance
  4. KPI Alerts & Trends
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlalchemy as sa
from datetime import datetime

# ─── Path setup ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "etl"))
from load import get_engine

# ─── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="KPI Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: white; border-radius: 10px; padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.1); text-align: center; margin-bottom: 8px;
  }
  .metric-card .value { font-size: 2rem; font-weight: 700; color: #3985D6; }
  .metric-card .label { font-size: .85rem; color: #64748b; margin-top: 4px; }
  .metric-card .delta-pos { font-size: .8rem; color: #16a34a; }
  .metric-card .delta-neg { font-size: .8rem; color: #dc2626; }
  .alert-crit { background:#fef2f2; border-left:4px solid #dc2626;
                padding:8px 14px; border-radius:0 6px 6px 0; margin:4px 0; }
  .alert-warn { background:#fefce8; border-left:4px solid #ca8a04;
                padding:8px 14px; border-radius:0 6px 6px 0; margin:4px 0; }
</style>
""", unsafe_allow_html=True)


# ─── Data loading ─────────────────────────────────────────────
@st.cache_resource
def get_db():
    return get_engine()

@st.cache_data(ttl=300)
def load_df(query: str) -> pd.DataFrame:
    engine = get_db()
    with engine.connect() as conn:
        return pd.read_sql(sa.text(query), conn)


# ─── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/combo-chart--v1.png", width=48)
    st.title("KPI Monitor")
    st.caption("Automated Business Analytics")

    page = st.radio("Navigation", [
        "📊 Executive Overview",
        "🎯 Sales & Campaigns",
        "⚙️ Operational Performance",
        "🚨 KPI Alerts & Trends",
    ])
    st.divider()
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")


# ═══════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════════════════════
if page == "📊 Executive Overview":
    st.title("📊 Executive Overview")
    st.caption("High-level business performance summary across all campaigns and agents.")

    # KPI snapshot
    snap = load_df("""
        SELECT
            COUNT(*) AS total_calls,
            SUM(is_connected) AS connected_calls,
            COUNT(DISTINCT lead_id) AS unique_leads_called
        FROM calls
    """).iloc[0]

    sales_snap = load_df("""
        SELECT
            COUNT(*) AS total_sales,
            ROUND(SUM(revenue), 2) AS total_revenue,
            ROUND(AVG(revenue), 2) AS avg_order_value,
            ROUND(AVG(acquisition_cost), 2) AS avg_cac
        FROM sales
    """).iloc[0]

    total_leads = load_df("SELECT COUNT(*) AS n FROM leads").iloc[0]["n"]
    conn_rate   = round(100.0 * snap["connected_calls"] / max(snap["total_calls"], 1), 2)
    conv_rate   = round(100.0 * sales_snap["total_sales"] / max(total_leads, 1), 2)
    roas        = round(sales_snap["total_revenue"] / max(
                        load_df("SELECT COALESCE(SUM(acquisition_cost),1) AS v FROM sales").iloc[0]["v"], 1), 2)

    # ── KPI Cards ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📞 Total Calls",   f"{int(snap['total_calls']):,}")
    with col2:
        st.metric("🔗 Connection Rate", f"{conn_rate}%",
                  delta=f"{'▲' if conn_rate >= 55 else '▼'} vs 55% target")
    with col3:
        st.metric("💰 Total Revenue", f"₹{sales_snap['total_revenue']:,.0f}")
    with col4:
        st.metric("🔄 Conversion Rate", f"{conv_rate}%",
                  delta=f"{'▲' if conv_rate >= 20 else '▼'} vs 20% target")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("👥 Total Leads", f"{int(total_leads):,}")
    with col6:
        st.metric("✅ Total Sales", f"{int(sales_snap['total_sales']):,}")
    with col7:
        st.metric("🛒 Avg Order Value", f"₹{sales_snap['avg_order_value']:,.0f}")
    with col8:
        st.metric("📈 ROAS", f"{roas}x")

    st.divider()

    # ── Monthly Revenue Trend ──
    monthly = load_df("""
        SELECT sale_month AS month,
               ROUND(SUM(revenue), 2) AS revenue,
               COUNT(*) AS sales
        FROM sales GROUP BY sale_month ORDER BY sale_month
    """)
    if not monthly.empty:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.subheader("Monthly Revenue Trend")
            fig = px.line(monthly, x="month", y="revenue",
                          markers=True, color_discrete_sequence=["#3985D6"])
            fig.update_layout(xaxis_title="Month", yaxis_title="Revenue (₹)",
                              hovermode="x unified", plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.subheader("Monthly Sales Volume")
            fig2 = px.bar(monthly, x="month", y="sales", color_discrete_sequence=["#16a34a"])
            fig2.update_layout(xaxis_title="Month", yaxis_title="Sales Count", plot_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)

    # ── Daily Call Volume ──
    daily = load_df("""
        SELECT call_date,
               COUNT(*) AS total_calls,
               SUM(is_connected) AS connected_calls
        FROM calls
        GROUP BY call_date
        ORDER BY call_date
        LIMIT 90
    """)
    if not daily.empty:
        st.subheader("Daily Call Volume (Last 90 Days)")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=daily["call_date"], y=daily["total_calls"],
                                  name="Total Calls", line=dict(color="#3985D6")))
        fig3.add_trace(go.Scatter(x=daily["call_date"], y=daily["connected_calls"],
                                  name="Connected", line=dict(color="#16a34a")))
        fig3.update_layout(hovermode="x unified", plot_bgcolor="white",
                           xaxis_title="Date", yaxis_title="Calls")
        st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PAGE 2 — SALES & CAMPAIGN ANALYSIS
# ═══════════════════════════════════════════════════════════════
elif page == "🎯 Sales & Campaigns":
    st.title("🎯 Sales & Campaign Analysis")
    st.caption("Deep-dive into campaign effectiveness, revenue contribution, and return on spend.")

    camp = load_df("""
        SELECT
            c.campaign_name,
            c.budget,
            COUNT(l.lead_id)         AS total_leads,
            COUNT(s.sale_id)         AS total_sales,
            ROUND(SUM(s.revenue),2)  AS total_revenue,
            ROUND(SUM(s.acquisition_cost),2) AS total_cac,
            ROUND(100.0 * COUNT(s.sale_id) / MAX(COUNT(l.lead_id), 1), 2) AS conv_rate,
            ROUND(SUM(s.revenue) / MAX(c.budget, 1), 2) AS roas
        FROM campaigns c
        LEFT JOIN leads l  ON c.campaign_id = l.campaign_id
        LEFT JOIN sales s  ON c.campaign_id = s.campaign_id
        GROUP BY c.campaign_id, c.campaign_name, c.budget
        ORDER BY total_revenue DESC
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenue by Campaign")
        fig = px.bar(camp, x="campaign_name", y="total_revenue",
                     color="total_revenue", color_continuous_scale="Blues",
                     labels={"campaign_name":"Campaign","total_revenue":"Revenue (₹)"})
        fig.update_layout(plot_bgcolor="white", showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Conversion Rate by Campaign (%)")
        fig2 = px.bar(camp, x="campaign_name", y="conv_rate",
                      color="conv_rate", color_continuous_scale="Greens",
                      labels={"campaign_name":"Campaign","conv_rate":"Conversion Rate (%)"})
        fig2.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Target 20%")
        fig2.update_layout(plot_bgcolor="white", showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Budget vs Revenue")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=camp["campaign_name"], y=camp["budget"],
                              name="Budget", marker_color="#94a3b8"))
        fig3.add_trace(go.Bar(x=camp["campaign_name"], y=camp["total_revenue"],
                              name="Revenue", marker_color="#3985D6"))
        fig3.update_layout(barmode="group", plot_bgcolor="white",
                           xaxis_title="Campaign", yaxis_title="Amount (₹)")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("ROAS by Campaign")
        fig4 = px.scatter(camp, x="total_cac", y="total_revenue",
                          size="total_sales", color="campaign_name",
                          hover_name="campaign_name",
                          labels={"total_cac":"Total CAC (₹)","total_revenue":"Revenue (₹)"})
        fig4.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Full Campaign Table")
    st.dataframe(camp, use_container_width=True)

    # Revenue by segment
    seg = load_df("""
        SELECT l.customer_segment,
               COUNT(s.sale_id)          AS total_sales,
               ROUND(SUM(s.revenue), 2)  AS revenue,
               ROUND(AVG(s.revenue), 2)  AS avg_revenue
        FROM sales s JOIN leads l ON s.lead_id = l.lead_id
        GROUP BY l.customer_segment ORDER BY revenue DESC
    """)
    st.divider()
    st.subheader("Revenue by Customer Segment")
    col5, col6 = st.columns(2)
    with col5:
        fig5 = px.pie(seg, values="revenue", names="customer_segment",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig5.update_layout(title="Revenue Share by Segment")
        st.plotly_chart(fig5, use_container_width=True)
    with col6:
        fig6 = px.bar(seg, x="customer_segment", y="avg_revenue",
                      color="customer_segment", color_discrete_sequence=px.colors.qualitative.Set2,
                      labels={"customer_segment":"Segment","avg_revenue":"Avg Revenue (₹)"})
        fig6.update_layout(plot_bgcolor="white", showlegend=False, title="Avg Revenue per Sale")
        st.plotly_chart(fig6, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PAGE 3 — OPERATIONAL PERFORMANCE
# ═══════════════════════════════════════════════════════════════
elif page == "⚙️ Operational Performance":
    st.title("⚙️ Operational Performance")
    st.caption("Agent productivity, call metrics, and team-level insights.")

    agents = load_df("""
        SELECT
            a.agent_name, a.team,
            COUNT(DISTINCT c.call_id)                    AS total_calls,
            SUM(c.is_connected)                          AS connected_calls,
            ROUND(100.0 * SUM(c.is_connected) / MAX(COUNT(c.call_id),1), 2) AS conn_rate,
            ROUND(AVG(c.call_duration) FILTER (WHERE c.call_status='Connected'), 0) AS avg_duration,
            COUNT(DISTINCT s.sale_id)                    AS total_sales,
            ROUND(COALESCE(SUM(s.revenue), 0), 2)        AS total_revenue
        FROM agents a
        JOIN calls c ON a.agent_id = c.agent_id
        LEFT JOIN sales s ON c.lead_id = s.lead_id
        GROUP BY a.agent_id, a.agent_name, a.team
        ORDER BY total_revenue DESC
    """)

    team_filter = st.multiselect("Filter by Team", agents["team"].unique().tolist(),
                                  default=agents["team"].unique().tolist())
    agents_f = agents[agents["team"].isin(team_filter)]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Agent Revenue Leaderboard")
        fig = px.bar(agents_f.head(15), x="total_revenue", y="agent_name",
                     orientation="h", color="team",
                     labels={"total_revenue":"Revenue (₹)","agent_name":"Agent"})
        fig.update_layout(plot_bgcolor="white", yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Connection Rate by Agent (%)")
        fig2 = px.bar(agents_f.sort_values("conn_rate"), x="conn_rate", y="agent_name",
                      orientation="h", color="conn_rate", color_continuous_scale="RdYlGn")
        fig2.add_vline(x=55, line_dash="dash", line_color="gray", annotation_text="55% target")
        fig2.update_layout(plot_bgcolor="white", yaxis={"categoryorder":"total ascending"},
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Call status distribution
    status_dist = load_df("""
        SELECT call_status, COUNT(*) AS cnt FROM calls GROUP BY call_status ORDER BY cnt DESC
    """)
    hour_perf = load_df("""
        SELECT call_hour,
               COUNT(*) AS total_calls,
               SUM(is_connected) AS connected,
               ROUND(100.0 * SUM(is_connected) / MAX(COUNT(*),1), 2) AS conn_rate
        FROM calls GROUP BY call_hour ORDER BY call_hour
    """)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Call Status Distribution")
        fig3 = px.pie(status_dist, values="cnt", names="call_status",
                      color_discrete_sequence=["#16a34a","#dc2626","#f59e0b","#6366f1"])
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Connection Rate by Hour of Day")
        fig4 = px.line(hour_perf, x="call_hour", y="conn_rate", markers=True,
                       color_discrete_sequence=["#3985D6"],
                       labels={"call_hour":"Hour","conn_rate":"Connection Rate (%)"})
        fig4.add_hline(y=55, line_dash="dash", line_color="red")
        fig4.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Team Performance Summary")
    team_perf = agents_f.groupby("team").agg(
        agents=("agent_name","count"),
        total_calls=("total_calls","sum"),
        total_sales=("total_sales","sum"),
        total_revenue=("total_revenue","sum"),
        avg_conn_rate=("conn_rate","mean"),
    ).reset_index()
    team_perf["avg_conn_rate"] = team_perf["avg_conn_rate"].round(2)
    st.dataframe(team_perf, use_container_width=True)

    st.subheader("Full Agent Scorecard")
    st.dataframe(agents_f, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PAGE 4 — KPI ALERTS & TRENDS
# ═══════════════════════════════════════════════════════════════
elif page == "🚨 KPI Alerts & Trends":
    st.title("🚨 KPI Alerts & Trends")
    st.caption("Historical KPI thresholds monitoring, deviations, and alert log.")

    # Month-over-month comparison
    mom = load_df("""
        SELECT sale_month AS month,
               COUNT(*) AS sales,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(AVG(acquisition_cost), 2) AS avg_cac
        FROM sales GROUP BY sale_month ORDER BY sale_month
    """)
    if not mom.empty:
        mom["prev_revenue"]     = mom["revenue"].shift(1)
        mom["revenue_growth"]   = round(
            100.0 * (mom["revenue"] - mom["prev_revenue"]) / mom["prev_revenue"].replace(0, float("nan")), 2
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Monthly Revenue with MoM Growth")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=mom["month"], y=mom["revenue"],
                                 name="Revenue", marker_color="#3985D6", yaxis="y"))
            fig.add_trace(go.Scatter(x=mom["month"], y=mom["revenue_growth"],
                                     name="MoM Growth %", mode="lines+markers",
                                     line=dict(color="#f59e0b"), yaxis="y2"))
            fig.update_layout(
                yaxis=dict(title="Revenue (₹)"),
                yaxis2=dict(title="Growth (%)", overlaying="y", side="right"),
                legend=dict(x=0, y=1), plot_bgcolor="white", hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Average CAC Over Time")
            fig2 = px.line(mom, x="month", y="avg_cac", markers=True,
                           color_discrete_sequence=["#dc2626"],
                           labels={"month":"Month","avg_cac":"Avg CAC (₹)"})
            fig2.add_hline(y=400, line_dash="dash", line_color="orange", annotation_text="Warning ₹400")
            fig2.add_hline(y=500, line_dash="dash", line_color="red",    annotation_text="Critical ₹500")
            fig2.update_layout(plot_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)

    # Daily connection rate trend
    daily_cr = load_df("""
        SELECT call_date,
               ROUND(100.0 * SUM(is_connected) / MAX(COUNT(*),1), 2) AS conn_rate
        FROM calls GROUP BY call_date ORDER BY call_date
    """)
    if not daily_cr.empty:
        st.subheader("Daily Connection Rate with Alert Thresholds")
        fig3 = px.line(daily_cr, x="call_date", y="conn_rate",
                       color_discrete_sequence=["#3985D6"],
                       labels={"call_date":"Date","conn_rate":"Connection Rate (%)"})
        fig3.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Warning 50%")
        fig3.add_hline(y=40, line_dash="dash", line_color="red",    annotation_text="Critical 40%")
        fig3.update_layout(plot_bgcolor="white", hovermode="x unified")
        st.plotly_chart(fig3, use_container_width=True)

    # Alert log
    st.subheader("🔔 Alert History")
    try:
        alerts_df = load_df("""
            SELECT alert_time, metric_name, actual_val, target_val, severity, message
            FROM kpi_alerts
            ORDER BY alert_time DESC
            LIMIT 50
        """)
        if alerts_df.empty:
            st.success("✅ No alerts have been triggered yet. Run the alert engine to populate.")
        else:
            for _, row in alerts_df.iterrows():
                cls = "alert-crit" if row["severity"] == "CRITICAL" else "alert-warn"
                st.markdown(
                    f'<div class="{cls}"><strong>[{row["severity"]}]</strong> '
                    f'{row["metric_name"]} = {row["actual_val"]} '
                    f'(target: {row["target_val"]}) — {row["alert_time"]}</div>',
                    unsafe_allow_html=True
                )
    except Exception:
        st.info("No alerts yet. Run `python automation/alert_engine.py` to populate.")

    # Campaign-wise conversion trend
    st.divider()
    st.subheader("Campaign Anomaly: CAC vs Revenue")
    camp_anom = load_df("""
        SELECT c.campaign_name,
               ROUND(AVG(s.acquisition_cost), 2) AS avg_cac,
               ROUND(SUM(s.revenue), 2) AS revenue,
               COUNT(s.sale_id) AS sales
        FROM sales s JOIN campaigns c ON s.campaign_id = c.campaign_id
        GROUP BY c.campaign_name
        ORDER BY avg_cac DESC
    """)
    fig4 = px.scatter(camp_anom, x="avg_cac", y="revenue", size="sales",
                      color="campaign_name", hover_name="campaign_name",
                      labels={"avg_cac":"Avg CAC (₹)","revenue":"Total Revenue (₹)"},
                      title="High CAC campaigns in upper-left are problematic")
    fig4.add_vline(x=400, line_dash="dash", line_color="orange", annotation_text="CAC Warning")
    fig4.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig4, use_container_width=True)

    st.info("💡 **Tip:** Campaigns with high CAC and low revenue are costing more than they earn. "
            "Review targeting and lead quality for those campaigns.")
