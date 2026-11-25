-- ============================================================
-- SQL Views — Reusable KPI Calculation Layer
-- ============================================================

-- ─── View 1: Daily Call Metrics ──────────────────────────────
CREATE OR REPLACE VIEW vw_daily_call_metrics AS
SELECT
    DATE(call_timestamp)                                                AS call_date,
    COUNT(*)                                                            AS total_calls,
    COUNT(*) FILTER (WHERE call_status = 'Connected')                  AS connected_calls,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE call_status = 'Connected')
        / NULLIF(COUNT(*), 0), 2
    )                                                                   AS connection_rate_pct,
    ROUND(AVG(call_duration) FILTER (WHERE call_status = 'Connected'), 0)
                                                                        AS avg_call_duration_sec,
    COUNT(DISTINCT agent_id)                                            AS active_agents
FROM calls
GROUP BY DATE(call_timestamp);


-- ─── View 2: Campaign KPI Summary ────────────────────────────
CREATE OR REPLACE VIEW vw_campaign_kpis AS
WITH cl AS (
    SELECT campaign_id, COUNT(*) AS total_leads FROM leads GROUP BY campaign_id
),
cs AS (
    SELECT campaign_id, COUNT(*) AS total_sales, SUM(revenue) AS total_revenue,
           SUM(acquisition_cost) AS total_cac
    FROM sales GROUP BY campaign_id
)
SELECT
    c.campaign_id,
    c.campaign_name,
    c.budget,
    cl.total_leads,
    COALESCE(cs.total_sales, 0)                                        AS total_sales,
    COALESCE(cs.total_revenue, 0)                                      AS total_revenue,
    COALESCE(cs.total_cac, 0)                                          AS total_cac,
    ROUND(100.0 * COALESCE(cs.total_sales,0) / NULLIF(cl.total_leads,0), 2)
                                                                        AS conversion_rate_pct,
    ROUND(COALESCE(cs.total_revenue, 0) / NULLIF(c.budget, 0), 2)     AS roas,
    ROUND(COALESCE(cs.total_cac,0) / NULLIF(COALESCE(cs.total_sales,0),0), 2)
                                                                        AS avg_cac
FROM campaigns c
JOIN cl  ON c.campaign_id = cl.campaign_id
LEFT JOIN cs ON c.campaign_id = cs.campaign_id;


-- ─── View 3: Agent Scorecard ─────────────────────────────────
CREATE OR REPLACE VIEW vw_agent_scorecard AS
WITH ac AS (
    SELECT agent_id,
           COUNT(*) AS total_calls,
           COUNT(*) FILTER (WHERE call_status = 'Connected') AS connected_calls,
           ROUND(AVG(call_duration) FILTER (WHERE call_status='Connected'), 0) AS avg_duration
    FROM calls GROUP BY agent_id
),
ags AS (
    SELECT c.agent_id, COUNT(DISTINCT s.sale_id) AS total_sales, SUM(s.revenue) AS total_revenue
    FROM calls c JOIN sales s ON c.lead_id = s.lead_id GROUP BY c.agent_id
)
SELECT
    a.agent_id, a.agent_name, a.team,
    ac.total_calls, ac.connected_calls,
    ROUND(100.0 * ac.connected_calls / NULLIF(ac.total_calls,0), 2) AS connection_rate_pct,
    ac.avg_duration                                                   AS avg_call_duration_sec,
    COALESCE(ags.total_sales, 0)                                      AS total_sales,
    COALESCE(ags.total_revenue, 0)                                    AS total_revenue,
    ROUND(COALESCE(ags.total_revenue,0) / NULLIF(ac.total_calls,0), 2) AS revenue_per_call
FROM agents a
JOIN ac ON a.agent_id = ac.agent_id
LEFT JOIN ags ON a.agent_id = ags.agent_id;


-- ─── View 4: Monthly Revenue Summary ─────────────────────────
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_TRUNC('month', sale_date)                            AS month,
    COUNT(*)                                                   AS total_sales,
    SUM(revenue)                                               AS total_revenue,
    ROUND(AVG(revenue), 2)                                     AS avg_revenue,
    SUM(acquisition_cost)                                      AS total_cac,
    ROUND(SUM(revenue) / NULLIF(SUM(acquisition_cost), 0), 2) AS roas
FROM sales
GROUP BY DATE_TRUNC('month', sale_date)
ORDER BY month;


-- ─── View 5: Segment Revenue ─────────────────────────────────
CREATE OR REPLACE VIEW vw_segment_revenue AS
SELECT
    l.customer_segment,
    COUNT(s.sale_id)         AS total_sales,
    SUM(s.revenue)           AS total_revenue,
    ROUND(AVG(s.revenue), 2) AS avg_revenue,
    ROUND(AVG(s.acquisition_cost), 2) AS avg_cac
FROM sales s
JOIN leads l ON s.lead_id = l.lead_id
GROUP BY l.customer_segment
ORDER BY total_revenue DESC;


-- ─── View 6: Overall KPI Snapshot ────────────────────────────
CREATE OR REPLACE VIEW vw_kpi_snapshot AS
SELECT
    (SELECT COUNT(*) FROM calls)                                      AS total_calls,
    (SELECT COUNT(*) FILTER (WHERE call_status='Connected') FROM calls)
                                                                       AS connected_calls,
    ROUND(
        100.0 * (SELECT COUNT(*) FILTER (WHERE call_status='Connected') FROM calls)
        / NULLIF((SELECT COUNT(*) FROM calls), 0), 2
    )                                                                  AS connection_rate_pct,
    (SELECT COUNT(*) FROM leads)                                       AS total_leads,
    (SELECT COUNT(*) FROM sales)                                       AS total_sales,
    ROUND(
        100.0 * (SELECT COUNT(*) FROM sales)
        / NULLIF((SELECT COUNT(*) FROM leads), 0), 2
    )                                                                  AS conversion_rate_pct,
    (SELECT SUM(revenue) FROM sales)                                   AS total_revenue,
    ROUND((SELECT AVG(revenue) FROM sales), 2)                         AS avg_order_value,
    ROUND((SELECT AVG(acquisition_cost) FROM sales), 2)               AS avg_cac,
    ROUND(
        (SELECT SUM(revenue) FROM sales)
        / NULLIF((SELECT SUM(acquisition_cost) FROM sales), 0), 2
    )                                                                  AS overall_roas;
