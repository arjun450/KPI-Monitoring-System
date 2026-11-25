-- ============================================================
-- KPI Monitoring System — Database Schema
-- Database: PostgreSQL 14+
-- ============================================================

CREATE DATABASE kpi_monitoring;
\c kpi_monitoring;

-- ─── AGENTS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agents (
    agent_id    SERIAL PRIMARY KEY,
    agent_name  VARCHAR(100) NOT NULL,
    team        VARCHAR(50)  NOT NULL,
    joining_date DATE,
    manager_id  INTEGER
);

-- ─── CAMPAIGNS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id   SERIAL PRIMARY KEY,
    campaign_name VARCHAR(150) NOT NULL,
    budget        NUMERIC(12,2),
    start_date    DATE,
    end_date      DATE,
    target_leads  INTEGER
);

-- ─── LEADS ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads (
    lead_id          SERIAL PRIMARY KEY,
    customer_segment VARCHAR(50),
    campaign_id      INTEGER REFERENCES campaigns(campaign_id),
    lead_created_at  TIMESTAMP NOT NULL,
    lead_source      VARCHAR(50),
    city             VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_leads_campaign_id ON leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_created_at  ON leads(lead_created_at);

-- ─── CALLS ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS calls (
    call_id        SERIAL PRIMARY KEY,
    lead_id        INTEGER NOT NULL REFERENCES leads(lead_id),
    agent_id       INTEGER NOT NULL REFERENCES agents(agent_id),
    call_timestamp TIMESTAMP NOT NULL,
    call_duration  INTEGER  DEFAULT 0 CHECK (call_duration >= 0),
    call_status    VARCHAR(30),   -- Connected | Not Connected | Busy | No Answer
    call_outcome   VARCHAR(30),   -- Interested | Not Interested | Follow-up | Converted
    call_hour      SMALLINT
);

CREATE INDEX IF NOT EXISTS idx_calls_lead_id    ON calls(lead_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent_id   ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_timestamp  ON calls(call_timestamp);
CREATE INDEX IF NOT EXISTS idx_calls_status     ON calls(call_status);

-- ─── SALES ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    sale_id          SERIAL PRIMARY KEY,
    lead_id          INTEGER NOT NULL REFERENCES leads(lead_id),
    campaign_id      INTEGER REFERENCES campaigns(campaign_id),
    sale_date        DATE NOT NULL,
    revenue          NUMERIC(12,2),
    acquisition_cost NUMERIC(12,2)
);

CREATE INDEX IF NOT EXISTS idx_sales_lead_id     ON sales(lead_id);
CREATE INDEX IF NOT EXISTS idx_sales_campaign_id ON sales(campaign_id);
CREATE INDEX IF NOT EXISTS idx_sales_date        ON sales(sale_date);

-- ─── ALERTS LOG ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kpi_alerts (
    alert_id    SERIAL PRIMARY KEY,
    alert_time  TIMESTAMP DEFAULT NOW(),
    metric_name VARCHAR(100),
    actual_val  NUMERIC(12,4),
    target_val  NUMERIC(12,4),
    deviation   NUMERIC(12,4),
    severity    VARCHAR(20),   -- WARNING | CRITICAL
    message     TEXT,
    resolved    BOOLEAN DEFAULT FALSE
);
