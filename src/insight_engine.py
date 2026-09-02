import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

ANOMALIES_PATH = Path(
    "data/processed/anomalies.csv"
)

CHANGE_POINTS_PATH = Path(
    "data/processed/change_points.csv"
)

SEASONAL_PATH = Path(
    "data/processed/seasonal_analysis.csv"
)

OUTPUT_PATH = Path(
    "data/processed/insights.csv"
)


# ============================================================
# METRIC INTERPRETATION
# ============================================================

METRIC_LABELS = {
    "activation": "activation",
    "conversion": "conversion",
    "retention": "retention",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_change_pct(value, baseline):
    """
    Calculate percentage change from baseline.
    """

    if pd.isna(baseline) or baseline == 0:
        return np.nan

    return ((value - baseline) / baseline) * 100


def format_percentage(value):
    """
    Convert a decimal metric value into a readable percentage.
    """

    if pd.isna(value):
        return "N/A"

    return f"{value * 100:.1f}%"


def get_direction_label(metric, direction):
    """
    Convert metric movement into a business interpretation.
    """

    if direction == "increase":
        return "positive"

    if direction == "decrease":
        return "concerning"

    return "neutral"


def get_priority(severity, direction):
    """
    Assign an actionable priority level.
    """

    if severity == "high":
        return "critical"

    if severity == "medium":
        return "high"

    if severity == "watch":
        return "medium"

    if severity == "positive":
        return "low"

    return "medium"


def build_recommendation(
    metric,
    direction,
    insight_type,
    severity
):
    """
    Generate a business recommendation.
    """

    if direction == "decrease":

        if metric == "activation":
            return (
                "Investigate onboarding and activation "
                "performance for this segment."
            )

        if metric == "conversion":
            return (
                "Investigate funnel performance and identify "
                "potential conversion blockers."
            )

        if metric == "retention":
            return (
                "Investigate churn drivers and recent "
                "changes affecting returning users."
            )

        return (
            "Investigate the cause of the downward movement."
        )

    if direction == "increase":

        if insight_type == "anomaly":
            return (
                "Validate the increase and identify the "
                "drivers behind the improvement."
            )

        if insight_type == "change_point":
            return (
                "Monitor the segment to determine whether "
                "the improvement is sustained."
            )

        return (
            "Monitor the segment for continued improvement."
        )

    return "Monitor this segment for further changes."


# ============================================================
# SEASONAL EVIDENCE
# ============================================================

def attach_seasonal_evidence(insights, seasonal):
    """
    Attach seasonal decomposition information to existing
    anomaly and change-point insights.

    Seasonal analysis is supporting evidence only.
    It does NOT create additional alerts.
    """

    if insights.empty or seasonal.empty:
        insights["seasonal_component"] = np.nan
        insights["seasonal_adjusted"] = np.nan
        insights["residual_z_score"] = np.nan
        insights["seasonality_context"] = "unavailable"

        return insights

    seasonal = seasonal.copy()

    seasonal["date"] = pd.to_datetime(
        seasonal["date"]
    )

    insights["date"] = pd.to_datetime(
        insights["date"]
    )

    seasonal_columns = [
        "date",
        "metric",
        "dimension",
        "segment",
        "seasonal",
        "seasonal_adjusted",
        "residual_z_score",
    ]

    seasonal_lookup = seasonal[
        seasonal_columns
    ].copy()

    # --------------------------------------------------------
    # Merge seasonal evidence onto existing insights.
    # --------------------------------------------------------

    insights = insights.merge(
        seasonal_lookup,
        on=[
            "date",
            "metric",
            "dimension",
            "segment",
        ],
        how="left"
    )

    # --------------------------------------------------------
    # Interpret seasonal evidence.
    #
    # Large residual z-score means the movement remains
    # unusual even after considering the seasonal pattern.
    # --------------------------------------------------------

    def classify_seasonality(row):

        residual_z = row["residual_z_score"]

        if pd.isna(residual_z):
            return "unavailable"

        if abs(residual_z) >= 2:
            return "unusual_after_seasonality"

        return "consistent_with_seasonality"

    insights["seasonality_context"] = (
        insights.apply(
            classify_seasonality,
            axis=1
        )
    )

    return insights


# ============================================================
# ANOMALY INSIGHTS
# ============================================================

def build_anomaly_insights(anomalies):
    """
    Convert detected anomalies into business-readable insights.
    """

    if anomalies.empty:
        return pd.DataFrame()

    rows = []

    for _, row in anomalies.iterrows():

        value = row["value"]
        baseline = row["rolling_mean"]

        change_pct = calculate_change_pct(
            value,
            baseline
        )

        metric = row["metric"]
        segment = row["segment"]
        dimension = row["dimension"]
        direction = row["anomaly_direction"]

        value_pct = format_percentage(value)

        if pd.isna(baseline):
            baseline_text = "N/A"
        else:
            baseline_text = format_percentage(baseline)

        # ----------------------------------------------------
        # Insight text
        # ----------------------------------------------------

        if direction == "decrease":

            insight = (
                f"{segment} {metric} dropped to "
                f"{value_pct}, compared with a recent "
                f"baseline of {baseline_text}."
            )

        elif direction == "increase":

            insight = (
                f"{segment} {metric} increased to "
                f"{value_pct}, compared with a recent "
                f"baseline of {baseline_text}."
            )

        else:

            insight = (
                f"{segment} {metric} showed an unusual "
                f"movement to {value_pct}."
            )

        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        confidence = row.get(
            "confidence",
            "watch"
        )

        if confidence == "high":
            severity = "high"

        elif confidence == "medium":
            severity = "medium"

        else:
            severity = "watch"

        # ----------------------------------------------------
        # Priority
        # ----------------------------------------------------

        priority = get_priority(
            severity,
            direction
        )

        # ----------------------------------------------------
        # Business interpretation
        # ----------------------------------------------------

        interpretation = get_direction_label(
            metric,
            direction
        )

        # ----------------------------------------------------
        # Recommendation
        # ----------------------------------------------------

        recommendation = build_recommendation(
            metric,
            direction,
            "anomaly",
            severity
        )

        rows.append({

            "date": row["date"],

            "metric": metric,

            "dimension": dimension,

            "segment": segment,

            "insight_type": "anomaly",

            "severity": severity,

            "priority": priority,

            "direction": direction,

            "interpretation": interpretation,

            "value": value,

            "baseline": baseline,

            "change_pct": change_pct,

            "sample_size": row["sample_size"],

            "confidence": confidence,

            "z_score": row["z_score"],

            "recommendation": recommendation,

            "insight": insight,
        })

    return pd.DataFrame(rows)


# ============================================================
# CHANGE-POINT INSIGHTS
# ============================================================

def build_change_point_insights(change_points):
    """
    Convert detected change points into business-readable insights.
    """

    if change_points.empty:
        return pd.DataFrame()

    rows = []

    for _, row in change_points.iterrows():

        metric = row["metric"]

        segment = row["segment"]

        dimension = row["dimension"]

        direction = row["change_direction"]

        value = row["value"]

        sample_size = row["sample_size"]

        value_pct = format_percentage(value)

        # ----------------------------------------------------
        # Ignore invalid directions
        # ----------------------------------------------------

        if direction not in [
            "increase",
            "decrease"
        ]:
            continue

        # ----------------------------------------------------
        # Business interpretation
        # ----------------------------------------------------

        interpretation = get_direction_label(
            metric,
            direction
        )

        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        if direction == "decrease":
            severity = "high"
        else:
            severity = "positive"

        # ----------------------------------------------------
        # Priority
        # ----------------------------------------------------

        priority = get_priority(
            severity,
            direction
        )

        # ----------------------------------------------------
        # Insight text
        # ----------------------------------------------------

        if direction == "increase":

            insight = (
                f"{segment} {metric} shows a sustained "
                f"upward shift around {value_pct}."
            )

        else:

            insight = (
                f"{segment} {metric} shows a sustained "
                f"downward shift around {value_pct}."
            )

        # ----------------------------------------------------
        # Recommendation
        # ----------------------------------------------------

        recommendation = build_recommendation(
            metric,
            direction,
            "change_point",
            severity
        )

        rows.append({

            "date": row["date"],

            "metric": metric,

            "dimension": dimension,

            "segment": segment,

            "insight_type": "change_point",

            "severity": severity,

            "priority": priority,

            "direction": direction,

            "interpretation": interpretation,

            "value": value,

            "baseline": np.nan,

            "change_pct": np.nan,

            "sample_size": sample_size,

            "confidence": row.get(
                "confidence",
                "detected"
            ),

            "z_score": np.nan,

            "recommendation": recommendation,

            "insight": insight,
        })

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "💡 Starting MetricPulse insight engine..."
    )

    # ========================================================
    # LOAD ANOMALIES
    # ========================================================

    anomalies = pd.read_csv(
        ANOMALIES_PATH
    )

    anomalies["date"] = pd.to_datetime(
        anomalies["date"]
    )

    anomalies = anomalies[
        anomalies["is_anomaly"] == True
    ].copy()

    print(
        f"🚨 Loaded {len(anomalies):,} anomalies"
    )

    # ========================================================
    # LOAD CHANGE POINTS
    # ========================================================

    change_points = pd.read_csv(
        CHANGE_POINTS_PATH
    )

    change_points["date"] = pd.to_datetime(
        change_points["date"]
    )

    change_points = change_points[
        change_points["is_change_point"] == True
    ].copy()

    print(
        f"🔎 Loaded {len(change_points):,} change points"
    )

    # ========================================================
    # LOAD SEASONAL ANALYSIS
    # ========================================================

    seasonal = pd.read_csv(
        SEASONAL_PATH
    )

    seasonal["date"] = pd.to_datetime(
        seasonal["date"]
    )

    print(
        f"🌱 Loaded {len(seasonal):,} seasonal observations"
    )

    # ========================================================
    # BUILD INSIGHTS
    # ========================================================

    anomaly_insights = build_anomaly_insights(
        anomalies
    )

    change_insights = build_change_point_insights(
        change_points
    )

    insights = pd.concat(
        [
            anomaly_insights,
            change_insights
        ],
        ignore_index=True
    )

    if insights.empty:
        raise ValueError(
            "No insights could be generated."
        )

    # ========================================================
    # ADD SEASONAL EVIDENCE
    # ========================================================

    insights = attach_seasonal_evidence(
        insights,
        seasonal
    )

    # ========================================================
    # CLEAN DATA
    # ========================================================

    insights["date"] = pd.to_datetime(
        insights["date"]
    ).dt.date

    numeric_columns = [
        "value",
        "baseline",
        "change_pct",
        "sample_size",
        "z_score",
        "seasonal_component",
        "seasonal_adjusted",
        "residual_z_score",
    ]

    for column in numeric_columns:

        if column in insights.columns:

            insights[column] = pd.to_numeric(
                insights[column],
                errors="coerce"
            )

    # ========================================================
    # SORT
    # ========================================================

    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    insights["_priority_order"] = (
        insights["priority"]
        .map(priority_order)
        .fillna(99)
    )

    insights = insights.sort_values(
        [
            "date",
            "_priority_order",
            "metric",
            "dimension",
            "segment",
            "insight_type",
        ]
    )

    insights = insights.drop(
        columns=["_priority_order"]
    )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    insights.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"\n✅ Created {len(insights):,} insights"
    )

    print(
        f"💾 Saved to {OUTPUT_PATH}"
    )

    print(
        "\n📊 Insights by type:"
    )

    print(
        insights.groupby(
            "insight_type"
        ).size()
    )

    print(
        "\n🚦 Insights by severity:"
    )

    print(
        insights.groupby(
            [
                "insight_type",
                "severity"
            ]
        ).size()
    )

    print(
        "\n🚨 Insights by priority:"
    )

    print(
        insights.groupby(
            "priority"
        ).size()
    )

    print(
        "\n📈 Insights by metric:"
    )

    print(
        insights.groupby(
            "metric"
        ).size()
    )

    print(
        "\n📉 Insights by direction:"
    )

    print(
        insights.groupby(
            "direction"
        ).size()
    )

    print(
        "\n📐 Insights by dimension:"
    )

    print(
        insights.groupby(
            "dimension"
        ).size()
    )

    print(
        "\n🌱 Seasonal context:"
    )

    print(
        insights.groupby(
            "seasonality_context"
        ).size()
    )

    print(
        "\n🎯 MetricPulse insight engine complete!"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()