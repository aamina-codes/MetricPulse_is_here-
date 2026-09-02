import pandas as pd
from pathlib import Path


ANOMALY_PATH = Path(
    "data/processed/anomalies.csv"
)

CHANGE_POINT_PATH = Path(
    "data/processed/change_points.csv"
)

OUTPUT_PATH = Path(
    "data/processed/insights.csv"
)


def build_anomaly_insights(anomalies):

    anomalies = anomalies[
        anomalies["is_anomaly"]
    ].copy()

    if anomalies.empty:
        return pd.DataFrame()

    insights = []

    for _, row in anomalies.iterrows():

        metric = row["metric"]
        dimension = row["dimension"]
        segment = row["segment"]

        value = float(row["value"])
        baseline = float(row["rolling_mean"])
        z_score = float(row["z_score"])

        direction = row["anomaly_direction"]
        confidence = row["confidence"]

        change_pct = (
            (value - baseline) / baseline * 100
            if baseline != 0
            else 0
        )

        if direction == "decrease":

            insight_text = (
                f"{segment} {metric} dropped to "
                f"{value:.1%}, compared with a recent "
                f"baseline of {baseline:.1%}."
            )

            severity = (
                "high"
                if confidence == "high"
                else "medium"
            )

        else:

            insight_text = (
                f"{segment} {metric} increased to "
                f"{value:.1%}, compared with a recent "
                f"baseline of {baseline:.1%}."
            )

            severity = (
                "positive"
                if confidence == "high"
                else "watch"
            )

        insights.append(
            {
                "date": row["date"],
                "metric": metric,
                "dimension": dimension,
                "segment": segment,
                "insight_type": "anomaly",
                "severity": severity,
                "direction": direction,
                "value": value,
                "baseline": baseline,
                "change_pct": change_pct,
                "sample_size": int(row["sample_size"]),
                "confidence": confidence,
                "z_score": z_score,
                "insight": insight_text,
            }
        )

    return pd.DataFrame(insights)


def build_change_point_insights(change_points):

    change_points = change_points[
        change_points["is_change_point"]
    ].copy()

    if change_points.empty:
        return pd.DataFrame()

    insights = []

    for _, row in change_points.iterrows():

        direction = row["change_direction"]

        metric = row["metric"]
        segment = row["segment"]

        value = float(row["value"])

        if direction == "increase":

            insight_text = (
                f"{segment} {metric} shows a sustained "
                f"upward shift around {value:.1%}."
            )

            severity = "positive"

        else:

            insight_text = (
                f"{segment} {metric} shows a sustained "
                f"downward shift around {value:.1%}."
            )

            severity = "high"

        insights.append(
            {
                "date": row["date"],
                "metric": metric,
                "dimension": row["dimension"],
                "segment": segment,
                "insight_type": "change_point",
                "severity": severity,
                "direction": direction,
                "value": value,
                "baseline": None,
                "change_pct": None,
                "sample_size": int(row["sample_size"]),
                "confidence": "detected",
                "z_score": None,
                "insight": insight_text,
            }
        )

    return pd.DataFrame(insights)


def main():

    print(
        "🧠 Building MetricPulse insight layer..."
    )

    anomalies = pd.read_csv(
        ANOMALY_PATH
    )

    change_points = pd.read_csv(
        CHANGE_POINT_PATH
    )

    print(
        f"📊 Loaded {len(anomalies):,} anomaly observations"
    )

    print(
        f"📊 Loaded {len(change_points):,} change-point observations"
    )

    anomaly_insights = build_anomaly_insights(
        anomalies
    )

    change_insights = build_change_point_insights(
        change_points
    )

    frames = []

    if not anomaly_insights.empty:
        frames.append(anomaly_insights)

    if not change_insights.empty:
        frames.append(change_insights)

    if not frames:
        raise ValueError(
            "No insights could be generated."
        )

    insights = pd.concat(
        frames,
        ignore_index=True
    )

    insights["date"] = pd.to_datetime(
        insights["date"]
    )

    insights = insights.sort_values(
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "insight_type",
        ]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    insights.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"\n💡 Created {len(insights):,} insights"
    )

    print(
        f"💾 Saved to {OUTPUT_PATH}"
    )

    print(
        "\n📈 Insights by type:"
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
            "severity"
        ).size()
    )

    print(
        "\n🔎 Sample insights:"
    )

    print(
        insights[
            [
                "date",
                "metric",
                "dimension",
                "segment",
                "insight_type",
                "severity",
                "confidence",
                "insight",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print(
        "\n✅ MetricPulse insight layer complete!"
    )


if __name__ == "__main__":
    main()