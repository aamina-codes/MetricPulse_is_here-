# 📊 MetricPulse — Product Health Monitor

> An automated product analytics system for detecting KPI anomalies, identifying meaningful metric shifts, and turning them into actionable product insights.

MetricPulse is an end-to-end product health monitoring pipeline designed to move beyond static KPI dashboards.

It analyzes product events, calculates key product metrics, detects unusual behavior, identifies structural changes, accounts for seasonality, and generates actionable insights that help product teams understand **what changed, where it changed, and what to investigate next.**

---

## About MetricPulse

MetricPulse was built around a simple question:

> **What if a product dashboard could tell you not only that a metric changed, but also whether the change was unusual, where it happened, and what you should investigate?**

Product metrics can move for many reasons.

A decline in retention might indicate a genuine product problem. A change in conversion could be isolated to a specific acquisition channel. An unusual activation pattern might simply be seasonal behavior.

MetricPulse brings these signals together into a single monitoring workflow.

The system currently monitors three core product metrics:

- **Activation**
- **Conversion**
- **Retention**

across multiple dimensions:

- **Platform**
- **Region**
- **Acquisition Channel**

---

## Core Features

| Feature | What it does |
|---|---|
| 📈 **Product KPI Monitoring** | Tracks activation, conversion, and retention across multiple product dimensions. |
| 🚨 **Anomaly Detection** | Identifies metric movements that significantly deviate from recent rolling baselines. |
| 📍 **Change-Point Detection** | Detects meaningful shifts in metric behavior that may indicate a sustained change. |
| 🌱 **Seasonality Analysis** | Separates trend and seasonal behavior from unexpected residual movement. |
| 🔍 **Segment Analysis** | Drills into platform, region, and acquisition-channel performance. |
| 💡 **Automated Insights** | Converts detected signals into interpretable product-health insights. |
| ⚠️ **Severity Classification** | Categorizes insights based on the significance of the detected movement. |
| 🎯 **Priority Classification** | Helps identify which issues deserve the most immediate attention. |
| 🧠 **Seasonal Context** | Distinguishes unusual movements from behavior that may be explained by seasonality. |
| 📝 **Actionable Recommendations** | Generates recommendations for further investigation based on detected patterns. |
| 📊 **Interactive Dashboard** | Provides an executive-facing Redash dashboard for monitoring product health. |
| 🔎 **Dashboard Filters** | Enables drill-down by date, metric, dimension, and segment. |

---

## How MetricPulse Works

MetricPulse follows an end-to-end analytics pipeline:

**1. Generate Product Data**  
Create users and product events representing realistic product activity.

**2. Build Metric Observations**  
Transform raw events into product-health metrics across different segments.

**3. Detect Anomalies**  
Compare observations against rolling baselines to identify unusual movements.

**4. Detect Change Points**  
Identify sustained shifts in metric behavior.

**5. Analyze Seasonality**  
Separate trend, seasonal patterns, and unexpected residual behavior.

**6. Generate Insights**  
Combine analytical signals into understandable product-health insights.

**7. Prioritize Findings**  
Assign severity, priority, direction, and confidence.

**8. Visualize Product Health**  
Surface the results through an interactive Redash dashboard.

```text
Users + Events
       │
       ▼
Data Generation
       │
       ▼
Metric Observation Builder
       │
       ▼
Metric Observations
       │
       ├───────────────┐
       ▼               ▼
Anomaly Detection   Change-Point Detection
       │               │
       └───────┬───────┘
               ▼
       Seasonality Analysis
               │
               ▼
         Insight Engine
               │
               ▼
          PostgreSQL
               │
               ▼
            Redash
               │
               ▼
     Product Health Dashboard

```
