"""
Synthetic Data Generator for KPI Monitoring System
Generates realistic business data for a sales operations company.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

# ─── Configuration ──────────────────────────────────────────────────────────
NUM_AGENTS     = 20
NUM_CAMPAIGNS  = 10
NUM_LEADS      = 10_000
NUM_CALLS      = 25_000
NUM_SALES      = 2_000
START_DATE     = datetime(2024, 1, 1)
END_DATE       = datetime(2024, 10, 31)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Helper ──────────────────────────────────────────────────────────────────
def rand_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def rand_dates(start, end, n):
    delta = end - start
    offsets = np.random.randint(0, int(delta.total_seconds()), size=n)
    return [start + timedelta(seconds=int(o)) for o in offsets]


# ─── 1. AGENTS ───────────────────────────────────────────────────────────────
first_names = ["Arjun","Priya","Rahul","Sneha","Vikram","Ananya","Rohan","Meera",
               "Amit","Divya","Suresh","Pooja","Nikhil","Kavya","Ravi","Shreya",
               "Karan","Nisha","Deepak","Anjali"]
last_names  = ["Sharma","Patel","Verma","Singh","Gupta","Kumar","Joshi","Agarwal",
               "Mehta","Reddy","Nair","Pillai","Iyer","Rao","Shah","Chopra",
               "Bose","Mukherjee","Ghosh","Banerjee"]
teams       = ["Alpha","Beta","Gamma","Delta"]
managers    = [1, 2, 3, 4]  # 4 managers

agents_data = []
for i in range(1, NUM_AGENTS + 1):
    joining = rand_date(datetime(2022, 1, 1), datetime(2024, 1, 1))
    agents_data.append({
        "agent_id":    i,
        "agent_name":  f"{first_names[i-1]} {last_names[i-1]}",
        "team":        random.choice(teams),
        "joining_date": joining.strftime("%Y-%m-%d"),
        "manager_id":  random.choice(managers)
    })
agents_df = pd.DataFrame(agents_data)


# ─── 2. CAMPAIGNS ─────────────────────────────────────────────────────────────
campaign_names = [
    "Q1 Outreach", "Spring Push", "Summer Blitz", "Monsoon Sale",
    "Q3 Expansion", "Festival Drive", "Year-End Rush", "New Product Launch",
    "Loyalty Reactivation", "Premium Upsell"
]
campaigns_data = []
for i in range(1, NUM_CAMPAIGNS + 1):
    start = rand_date(START_DATE, START_DATE + timedelta(days=180))
    end   = start + timedelta(days=random.randint(30, 90))
    budget = round(random.uniform(50_000, 500_000), 2)
    campaigns_data.append({
        "campaign_id":   i,
        "campaign_name": campaign_names[i-1],
        "budget":        budget,
        "start_date":    start.strftime("%Y-%m-%d"),
        "end_date":      end.strftime("%Y-%m-%d"),
        "target_leads":  random.randint(500, 2000)
    })
campaigns_df = pd.DataFrame(campaigns_data)


# ─── 3. LEADS ────────────────────────────────────────────────────────────────
segments = ["SME", "Enterprise", "Retail", "Individual", "Government"]
sources  = ["Website", "Referral", "Cold Call", "Social Media", "Email"]

leads_dates = rand_dates(START_DATE, END_DATE, NUM_LEADS)
leads_data = []
for i in range(1, NUM_LEADS + 1):
    leads_data.append({
        "lead_id":          i,
        "customer_segment": random.choice(segments),
        "campaign_id":      random.randint(1, NUM_CAMPAIGNS),
        "lead_created_at":  leads_dates[i-1].strftime("%Y-%m-%d %H:%M:%S"),
        "lead_source":      random.choice(sources),
        "city":             random.choice(["Mumbai","Delhi","Bangalore","Chennai","Hyderabad",
                                           "Pune","Kolkata","Ahmedabad","Jaipur","Lucknow"])
    })
leads_df = pd.DataFrame(leads_data)


# ─── 4. CALLS ────────────────────────────────────────────────────────────────
call_statuses  = ["Connected", "Not Connected", "Busy", "No Answer"]
call_outcomes  = ["Interested", "Not Interested", "Follow-up", "Converted", "Voicemail"]
# Weight: Connected=55%, Not Connected=25%, Busy=12%, No Answer=8%
status_weights = [0.55, 0.25, 0.12, 0.08]

# Introduce anomalies for interesting analysis
# Campaign 3 ("Summer Blitz") will have declining conversion
# Agent 5 will have unusually low productivity
# After 2024-08-01 connection rate will dip

calls_data = []
call_dates = rand_dates(START_DATE, END_DATE, NUM_CALLS)
for i in range(1, NUM_CALLS + 1):
    lead_id  = random.randint(1, NUM_LEADS)
    agent_id = random.randint(1, NUM_AGENTS)
    ts       = call_dates[i-1]

    # Agent 5 anomaly: fewer connections
    if agent_id == 5:
        status = np.random.choice(call_statuses, p=[0.30, 0.45, 0.15, 0.10])
    # Dip in connection rate after August
    elif ts >= datetime(2024, 8, 1):
        status = np.random.choice(call_statuses, p=[0.42, 0.35, 0.14, 0.09])
    else:
        status = np.random.choice(call_statuses, p=status_weights)

    if status == "Connected":
        duration = random.randint(60, 900)
        outcome  = np.random.choice(call_outcomes, p=[0.30, 0.35, 0.20, 0.10, 0.05])
    else:
        duration = random.randint(0, 30)
        outcome  = "Not Reached"

    calls_data.append({
        "call_id":        i,
        "lead_id":        lead_id,
        "agent_id":       agent_id,
        "call_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "call_duration":  duration,
        "call_status":    status,
        "call_outcome":   outcome,
        "call_hour":      ts.hour
    })
calls_df = pd.DataFrame(calls_data)


# ─── 5. SALES ────────────────────────────────────────────────────────────────
# Pick 2000 leads that converted
converted_leads = random.sample(range(1, NUM_LEADS + 1), NUM_SALES)
sales_data = []
for i, lead_id in enumerate(converted_leads, start=1):
    lead     = leads_df[leads_df["lead_id"] == lead_id].iloc[0]
    lead_dt  = datetime.strptime(lead["lead_created_at"], "%Y-%m-%d %H:%M:%S")
    sale_dt  = lead_dt + timedelta(days=random.randint(1, 30))

    # Campaign 3 ("Summer Blitz") has higher CAC (problem scenario)
    campaign_id = int(lead["campaign_id"])
    if campaign_id == 3:
        acq_cost = round(random.uniform(400, 700), 2)
    else:
        acq_cost = round(random.uniform(100, 400), 2)

    # Enterprise segment has higher revenue
    segment = lead["customer_segment"]
    if segment == "Enterprise":
        revenue = round(random.uniform(5000, 20000), 2)
    elif segment == "SME":
        revenue = round(random.uniform(2000, 8000), 2)
    else:
        revenue = round(random.uniform(500, 3000), 2)

    sales_data.append({
        "sale_id":          i,
        "lead_id":          lead_id,
        "campaign_id":      campaign_id,
        "sale_date":        sale_dt.strftime("%Y-%m-%d"),
        "revenue":          revenue,
        "acquisition_cost": acq_cost
    })
sales_df = pd.DataFrame(sales_data)


# ─── Save to CSV ─────────────────────────────────────────────────────────────
agents_df.to_csv(f"{OUTPUT_DIR}/agents.csv",     index=False)
campaigns_df.to_csv(f"{OUTPUT_DIR}/campaigns.csv", index=False)
leads_df.to_csv(f"{OUTPUT_DIR}/leads.csv",       index=False)
calls_df.to_csv(f"{OUTPUT_DIR}/calls.csv",       index=False)
sales_df.to_csv(f"{OUTPUT_DIR}/sales.csv",       index=False)

print("✅  Data generation complete!")
print(f"   Agents:    {len(agents_df):>6,}")
print(f"   Campaigns: {len(campaigns_df):>6,}")
print(f"   Leads:     {len(leads_df):>6,}")
print(f"   Calls:     {len(calls_df):>6,}")
print(f"   Sales:     {len(sales_df):>6,}")
print(f"\n📂 Files saved to: {OUTPUT_DIR}")
