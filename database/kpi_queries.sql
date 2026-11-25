-- ============================================================
-- KPI Calculation Queries — Automated Business KPI Monitoring
-- ============================================================

-- ─── 1. DAILY CALL KPIs ──────────────────────────────────────
SELECT
    DATE(call_timestamp)                                        AS call_date,
    COUNT(*)                                                    AS total_calls,
    COUNT(*) FILTER (WHERE call_status = 'Connected')          AS connected_calls,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE call_status = 'Connected')
        / NULLIF(COUNT(*), 0), 2
    )                                                           AS connection_rate_pct,
    AVG(call_duration) FILTER (WHERE call_status = 'Connected') AS avg_call_duration_sec,
    COUNT(DISTINCT agent_id)                                    AS active_agents
FROM calls
GROUP BY DATE(call_timestamp)
ORDER BY call_date;


-- ─── 2. CONVERSION RATE BY CAMPAIGN ─────────────────────────
WITH campaign_leads AS (
    SELECT campaign_id, COUNT(*) AS total_leads
    FROM leads
    GROUP BY campaign_id
),
campaign_sales AS (
    SELECT campaign_id, COUNT(*) AS total_sales, SUM(revenue) AS total_revenue
    FROM sales
    GROUP BY campaign_id
)
SELECT
    c.campaign_id,
    c.campaign_name,
    cl.total_leads,
    COALESCE(cs.total_sales,  0)                           AS total_sales,
    COALESCE(cs.total_revenue, 0)                          AS total_revenue,
    ROUND(
        100.0 * COALESCE(cs.total_sales, 0)
        / NULLIF(cl.total_leads, 0), 2
    )                                                       AS conversion_rate_pct,
    c.budget,
    ROUND(
        COALESCE(cs.total_revenue, 0) / NULLIF(c.budget, 0), 2
    )                                                       AS roas
FROM campaigns c
JOIN campaign_leads cl  ON c.campaign_id = cl.campaign_id
LEFT JOIN campaign_sales cs ON c.campaign_id = cs.campaign_id
ORDER BY total_revenue DESC;


-- ─── 3. AGENT PERFORMANCE SCORECARD ─────────────────────────
WITH agent_calls AS (
    SELECT
        agent_id,
        COUNT(*)                                                   AS total_calls,
        COUNT(*) FILTER (WHERE call_status = 'Connected')         AS connected_calls,
        ROUND(AVG(call_duration) FILTER (WHERE call_status = 'Connected'), 0)
                                                                   AS avg_duration_sec,
        COUNT(DISTINCT DATE(call_timestamp))                       AS active_days
    FROM calls
    GROUP BY agent_id
),
agent_sales AS (
    SELECT c.agent_id, COUNT(DISTINCT s.sale_id) AS total_sales, SUM(s.revenue) AS total_revenue
    FROM calls c
    JOIN sales s ON c.lead_id = s.lead_id
    GROUP BY c.agent_id
)
SELECT
    a.agent_id,
    a.agent_name,
    a.team,
    ac.total_calls,
    ac.connected_calls,
    ROUND(100.0 * ac.connected_calls / NULLIF(ac.total_calls, 0), 2) AS connection_rate_pct,
    COALESCE(ags.total_sales, 0)                                      AS total_sales,
    COALESCE(ags.total_revenue, 0)                                    AS total_revenue,
    ROUND(COALESCE(ags.total_revenue, 0) / NULLIF(ac.total_calls, 0), 2) AS revenue_per_call,
    ac.active_days,
    ROUND(ac.total_calls::numeric / NULLIF(ac.active_days, 0), 1)   AS calls_per_day
FROM agents a
JOIN agent_calls ac  ON a.agent_id = ac.agent_id
LEFT JOIN agent_sales ags ON a.agent_id = ags.agent_id
ORDER BY total_revenue DESC;


-- ─── 4. MONTHLY KPI SUMMARY ──────────────────────────────────
SELECT
    DATE_TRUNC('month', call_timestamp)                          AS month,
    COUNT(*)                                                      AS total_calls,
    COUNT(*) FILTER (WHERE call_status = 'Connected')            AS connected_calls,
    ROUND(100.0 * COUNT(*) FILTER (WHERE call_status = 'Connected') / NULLIF(COUNT(*),0), 2)
                                                                  AS connection_rate_pct
FROM calls
GROUP BY DATE_TRUNC('month', call_timestamp)
ORDER BY month;


-- ─── 5. CUSTOMER ACQUISITION COST BY CAMPAIGN ───────────────
SELECT
    c.campaign_name,
    COUNT(s.sale_id)                                   AS total_sales,
    SUM(s.acquisition_cost)                            AS total_acquisition_spend,
    ROUND(AVG(s.acquisition_cost), 2)                  AS avg_cac,
    SUM(s.revenue)                                     AS total_revenue,
    ROUND(SUM(s.revenue) / NULLIF(SUM(s.acquisition_cost), 0), 2) AS roas
FROM sales s
JOIN campaigns c ON s.campaign_id = c.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY avg_cac DESC;


-- ─── 6. REVENUE BY CUSTOMER SEGMENT ─────────────────────────
SELECT
    l.customer_segment,
    COUNT(s.sale_id)         AS total_sales,
    SUM(s.revenue)           AS total_revenue,
    ROUND(AVG(s.revenue), 2) AS avg_revenue_per_sale,
    ROUND(AVG(s.acquisition_cost), 2) AS avg_cac
FROM sales s
JOIN leads l ON s.lead_id = l.lead_id
GROUP BY l.customer_segment
ORDER BY total_revenue DESC;


-- ─── 7. CALL PERFORMANCE BY HOUR OF DAY ─────────────────────
SELECT
    call_hour,
    COUNT(*)                                                      AS total_calls,
    COUNT(*) FILTER (WHERE call_status = 'Connected')            AS connected_calls,
    ROUND(100.0 * COUNT(*) FILTER (WHERE call_status = 'Connected') / NULLIF(COUNT(*),0), 2)
                                                                  AS connection_rate_pct,
    COUNT(*) FILTER (WHERE call_outcome = 'Converted')           AS conversions
FROM calls
GROUP BY call_hour
ORDER BY call_hour;


-- ─── 8. MONTH-OVER-MONTH KPI COMPARISON (Window Function) ───
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', sale_date)   AS month,
        COUNT(*)                         AS sales,
        SUM(revenue)                     AS revenue,
        AVG(acquisition_cost)            AS avg_cac
    FROM sales
    GROUP BY DATE_TRUNC('month', sale_date)
)
SELECT
    month,
    sales,
    revenue,
    ROUND(avg_cac, 2)                                            AS avg_cac,
    LAG(revenue) OVER (ORDER BY month)                           AS prev_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2
    )                                                            AS revenue_growth_pct
FROM monthly
ORDER BY month;


-- ─── 9. AGENT PERFORMANCE RANKING (Window Function) ─────────
WITH agent_rev AS (
    SELECT
        a.agent_name,
        a.team,
        SUM(s.revenue) AS total_revenue
    FROM agents a
    JOIN calls c  ON a.agent_id = c.agent_id
    JOIN sales s  ON c.lead_id  = s.lead_id
    GROUP BY a.agent_id, a.agent_name, a.team
)
SELECT
    agent_name,
    team,
    total_revenue,
    RANK()       OVER (ORDER BY total_revenue DESC)          AS overall_rank,
    RANK()       OVER (PARTITION BY team ORDER BY total_revenue DESC) AS team_rank,
    NTILE(4)     OVER (ORDER BY total_revenue DESC)          AS quartile
FROM agent_rev
ORDER BY overall_rank;


-- ─── 10. CAMPAIGNS WITH DECLINING CONVERSION ─────────────────
WITH monthly_conv AS (
    SELECT
        s.campaign_id,
        DATE_TRUNC('month', s.sale_date)  AS month,
        COUNT(s.sale_id)                  AS sales_count,
        COUNT(l.lead_id)                  AS leads_count
    FROM sales s
    JOIN leads l ON s.lead_id = l.lead_id AND l.campaign_id = s.campaign_id
    GROUP BY s.campaign_id, DATE_TRUNC('month', s.sale_date)
),
with_rate AS (
    SELECT *,
        ROUND(100.0 * sales_count / NULLIF(leads_count, 0), 2) AS conversion_rate,
        LAG(ROUND(100.0 * sales_count / NULLIF(leads_count, 0), 2))
            OVER (PARTITION BY campaign_id ORDER BY month)      AS prev_month_rate
    FROM monthly_conv
)
SELECT
    c.campaign_name,
    w.month,
    w.conversion_rate,
    w.prev_month_rate,
    ROUND(w.conversion_rate - w.prev_month_rate, 2) AS change_pp
FROM with_rate w
JOIN campaigns c ON w.campaign_id = c.campaign_id
WHERE w.prev_month_rate IS NOT NULL
ORDER BY change_pp ASC
LIMIT 20;
