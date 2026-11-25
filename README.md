# 📊 Automated Business KPI Monitoring & Reporting System

> **Project type:** Business Analyst Portfolio Project  
> **Tech stack:** Python · Pandas · SQL (SQLite / PostgreSQL) · Streamlit · SQLAlchemy  
> **Domain:** Sales Operations Analytics  

---

## 🎯 Project Overview

This system automates the end-to-end process of collecting business data, processing it through an ETL pipeline, calculating key performance indicators (KPIs), surfacing insights via an interactive dashboard, and alerting management when KPIs deviate from targets.

### Business scenario

A company uses AI-powered voice calls to generate sales. Thousands of calls are made daily to potential customers across multiple campaigns. Previously, employees manually collected data from different sources and prepared Excel reports — a slow process that caused management to identify problems too late.

**Solution:** A centralized automated reporting system with:
- **Python ETL pipeline** that cleans and loads data daily
- **SQL analytics layer** that calculates all KPIs
- **Streamlit dashboard** with 4 pages of interactive charts
- **Alert engine** that detects KPI breaches automatically
- **HTML report generator** for daily email-ready summaries

---

## 📁 Project Structure

```
KPI-Monitoring-System/
├── data/
│   ├── raw/                  ← CSV source files (auto-generated)
│   │   ├── agents.csv
│   │   ├── campaigns.csv
│   │   ├── leads.csv
│   │   ├── calls.csv
│   │   └── sales.csv
│   ├── processed/            ← Cleaned/processed outputs
│   ├── kpi_monitoring.db     ← SQLite database (auto-created)
│   └── generate_data.py      ← Synthetic data generator
│
├── database/
│   ├── create_tables.sql     ← PostgreSQL DDL schema
│   ├── kpi_queries.sql       ← All KPI SQL queries (10 queries)
│   └── create_views.sql      ← Reusable SQL views (6 views)
│
├── etl/
│   ├── extract.py            ← Read CSVs
│   ├── validate.py           ← Data quality checks
│   ├── transform.py          ← Add derived columns
│   └── load.py               ← Write to SQLite/PostgreSQL
│
├── automation/
│   ├── alert_engine.py       ← KPI threshold monitoring
│   ├── generate_report.py    ← HTML report generator
│   └── scheduler.py          ← Orchestrates full pipeline
│
├── dashboard/
│   └── app.py                ← Streamlit interactive dashboard
│
├── analysis/
│   └── exploratory_analysis.ipynb  ← Jupyter EDA notebook
│
├── reports/                  ← Auto-generated HTML reports
├── config/
│   └── thresholds.yaml       ← Alert thresholds config
├── setup_and_run.py          ← One-click setup script
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. One-click setup (generates data + runs ETL + launches dashboard)

```bash
python setup_and_run.py
```

### Or run each step manually:

```bash
# Step 1: Generate synthetic dataset
python data/generate_data.py

# Step 2: Run ETL pipeline
python etl/load.py

# Step 3: Run alert engine
python automation/alert_engine.py

# Step 4: Generate HTML report
python automation/generate_report.py

# Step 5: Launch dashboard
streamlit run dashboard/app.py
```

---

## 🗄️ Database Schema

Five relational tables forming a star-like schema:

```
AGENTS ──────────────────────────────────► CALLS ◄──── LEADS ◄──── CAMPAIGNS
                                            │               │
                                            └──────────────► SALES
```

| Table | Rows | Description |
|---|---|---|
| `agents` | 20 | Sales agents / employees |
| `campaigns` | 10 | Marketing campaigns |
| `leads` | 10,000 | Potential customers |
| `calls` | 25,000 | Call attempts (fact table) |
| `sales` | 2,000 | Successful conversions |

---

## 📈 KPIs Tracked

### Sales KPIs
| KPI | Formula |
|---|---|
| Connection Rate | Connected Calls / Total Calls × 100 |
| Conversion Rate | Converted Leads / Total Leads × 100 |
| Total Revenue | SUM(revenue) |
| Average Order Value | Revenue / Sales Count |
| Customer Acquisition Cost | SUM(acquisition_cost) / Sales Count |
| ROAS | Revenue / Campaign Budget |

### Operational KPIs
- Average call duration per agent
- Calls per agent per day
- Connection rate by hour of day
- Team performance comparison

### Financial KPIs
- Revenue by campaign
- Month-over-month revenue growth
- Budget vs actual revenue
- Campaign-level ROAS

---

## 🚨 Alert Thresholds

Configured in `config/thresholds.yaml`:

| KPI | Warning | Critical |
|---|---|---|
| Connection Rate | < 50% | < 40% |
| Conversion Rate | < 5% | < 3% |
| Avg CAC | > ₹400 | > ₹500 |
| ROAS | < 2x | < 1x |
| Revenue Drop (MoM) | > 10% | > 20% |

---

## 📊 Dashboard Pages

| Page | Contents |
|---|---|
| **Executive Overview** | KPI cards, monthly revenue trend, daily call volume |
| **Sales & Campaigns** | Campaign revenue, conversion rates, segment analysis |
| **Operational Performance** | Agent leaderboard, team comparison, hourly patterns |
| **KPI Alerts & Trends** | MoM comparison, threshold charts, alert history |

---

## 🔍 Key Business Insights (from synthetic data)

| Finding | Recommendation |
|---|---|
| **Summer Blitz** campaign has abnormally high CAC | Review targeting and reduce spend |
| **Agent 5** has ~30% connection rate vs 55% avg | Coaching + call schedule adjustment |
| **Connection rate dipped post-August 2024** | Audit lead list quality |
| **Enterprise segment** generates highest revenue | Prioritise in future campaigns |
| **Evening hours** show better connection rates | Increase evening call allocation |

---

## 🛠️ Using PostgreSQL (Optional)

By default the system uses SQLite (no server needed). To use PostgreSQL:

```bash
# Set environment variable before running any script
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/kpi_monitoring"

# Then run as normal
python setup_and_run.py
```

Create the PostgreSQL schema first:
```bash
psql -U postgres -f database/create_tables.sql
psql -U postgres -d kpi_monitoring -f database/create_views.sql
```

---

## 📄 Resume Bullet Points

> *Developed an automated ETL pipeline using Python and Pandas to extract, clean, validate, and load business data (10,000 leads, 25,000 calls, 2,000 sales) into a relational database.*  
> *Designed relational database schemas and SQL queries using joins, CTEs, aggregations, and window functions to calculate 15+ business KPIs.*  
> *Built a 4-page interactive Streamlit dashboard to monitor sales performance, conversion rates, revenue trends, and agent productivity.*  
> *Implemented automated KPI threshold monitoring with configurable alert rules (WARNING/CRITICAL) and HTML report generation.*  
> *Identified 5 actionable business insights from data including campaign CAC anomalies, agent performance gaps, and time-of-day conversion patterns.*

---

## ⚙️ Scheduling (Windows Task Scheduler)

To run the full pipeline daily at 8 AM:

1. Open **Task Scheduler** → Create Basic Task
2. Set trigger: **Daily at 08:00**
3. Set action: **Start a program**
   - Program: `python`
   - Arguments: `C:\path\to\KPI-Monitoring-System\automation\scheduler.py`
   - Start in: `C:\path\to\KPI-Monitoring-System`

---

> **Note:** Never commit credentials to GitHub. Use a `.env` file and add it to `.gitignore`.
