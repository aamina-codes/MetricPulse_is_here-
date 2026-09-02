import pandas as pd
import numpy as np
from pathlib import Path


INPUT_PATH = Path(
    "data/processed/metric_observations.csv"
)

OUTPUT_PATH = Path(
    "data/processed/anomalies.csv"
)

ROLLING_WINDOW = 7
Z_THRESHOLD = 2.5
MIN_SAMPLE_SIZE = 10


def calculate_anomalies(group):

    group = group.sort_values("date").copy()

    # Historical baseline.
    # shift(1) ensures today's value is NOT used
    # to calculate today's baseline.
    group["rolling_mean"] = (
        group["value"]
        .shift(1)
        .rolling(
            ROLLING_WINDOW,
            min_periods=4
        )
        .mean()
    )

    group["rolling_std"] = (
        group["value"]
        .shift(1)
        .rolling(
            ROLLING_WINDOW,
            min_periods=4
        )
        .std()
    )

    group["z_score"] = (
        (group["value"] - group["rolling_mean"])
        / group["rolling_std"].replace(0, np.nan)
    )

    group["anomaly_direction"] = np.select(
        [
            group["z_score"] < -Z_THRESHOLD,
            group["z_score"] > Z_THRESHOLD,
        ],
        [
            "decrease",
            "increase",
        ],
        default="normal",
    )

    # Don't trust very small cohorts.
    group.loc[
        group["sample_size"] < MIN_SAMPLE_SIZE,
        "anomaly_direction"
    ] = "insufficient_sample"

    group["is_anomaly"] = (
        group["anomaly_direction"].isin(
            ["decrease", "increase"]
        )
    )

# ---------------------------------------
# Anomaly confidence
# ---------------------------------------

    # ---------------------------------------
# Anomaly confidence
# ---------------------------------------

    group["confidence"] = "normal"

    high_confidence = (
    group["is_anomaly"]
    & (group["z_score"].abs() >= 3.0)
    & (group["sample_size"] >= 15)
)

    medium_confidence = (
        group["is_anomaly"]
    & (group["z_score"].abs() >= 2.5)
    & (group["sample_size"] >= 10)
)

    group.loc[
    medium_confidence,
    "confidence"
] = "medium"

    group.loc[
    high_confidence,
    "confidence"
] = "high"

# Small samples get downgraded
    group.loc[
    (group["is_anomaly"])
    & (group["sample_size"] < 15),
    "confidence"
] = "low_confidence"

    return group 

def main():

    print("🚀 Starting MetricPulse anomaly detection...")

    df = pd.read_csv(INPUT_PATH)

    df["date"] = pd.to_datetime(df["date"])

    print(
        f"📊 Loaded {len(df):,} observations"
    )

groups = []

df = pd.read_csv(INPUT_PATH)
for (metric, dimension, segment), group in df.groupby(
    ["metric", "dimension", "segment"]
):
    result = calculate_anomalies(group)

    result["metric"] = metric
    result["dimension"] = dimension
    result["segment"] = segment

    groups.append(result)

results = pd.concat(
    groups,
    ignore_index=True
)

anomalies = results[
        results["is_anomaly"]
    ].copy()

anomalies = anomalies.sort_values(
        [
            "date",
            "metric",
            "dimension",
            "segment",
        ]
    )

OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

results.to_csv(
        OUTPUT_PATH,
        index=False,
    )

print(
        f"\n🚨 {len(anomalies)} anomalies detected"
    )

if len(anomalies) > 0:

        print(
            "\nAnomaly summary:\n"
        )

        print(
            anomalies[
                [
                    "date",
                    "metric",
                    "dimension",
                    "segment",
                    "value",
                    "sample_size",
                    "rolling_mean",
                    "z_score",
                    "anomaly_direction",
                    "confidence",
                ]
            ]
            .round(4)
            .to_string(index=False)
        )

print(
        f"\n💾 Saved results to {OUTPUT_PATH}"
    )

print(
        "\n📈 Anomalies by metric:"
    )

print(
        anomalies.groupby(
            "metric"
        ).size()
    )

print(
        "\n📍 Anomalies by dimension:"
    )

print(
        anomalies.groupby(
            "dimension"
        ).size()
    )

print(
        "\n✅ MetricPulse anomaly detection complete!"
    )


if __name__ == "__main__":
    main()