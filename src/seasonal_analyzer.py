import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.tsa.seasonal import seasonal_decompose


INPUT_PATH = Path(
    "data/processed/metric_observations.csv"
)

OUTPUT_PATH = Path(
    "data/processed/seasonal_analysis.csv"
)

SEASONAL_PERIOD = 7
MIN_OBSERVATIONS = 21


def analyze_series(group):

    group = group.sort_values("date").copy()

    group["date"] = pd.to_datetime(group["date"])

    series = (
        group
        .set_index("date")["value"]
        .asfreq("D")
    )

    # Interpolate missing dates so decomposition
    # receives a continuous daily time series.
    series = series.interpolate(
        method="linear",
        limit_direction="both"
    )

    if len(series) < MIN_OBSERVATIONS:
        return None

    try:

        decomposition = seasonal_decompose(
            series,
            model="additive",
            period=SEASONAL_PERIOD,
            extrapolate_trend="freq"
        )

    except ValueError:
        return None

    result = pd.DataFrame({
        "date": series.index,
        "observed": decomposition.observed,
        "trend": decomposition.trend,
        "seasonal": decomposition.seasonal,
        "residual": decomposition.resid,
    })

    result["metric"] = group["metric"].iloc[0]
    result["dimension"] = group["dimension"].iloc[0]
    result["segment"] = group["segment"].iloc[0]

    result["residual_z_score"] = (
        result["residual"]
        - result["residual"].mean()
    ) / result["residual"].std()

    result["seasonal_adjusted"] = (
        result["observed"]
        - result["seasonal"]
    )

    return result[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "observed",
            "trend",
            "seasonal",
            "residual",
            "residual_z_score",
            "seasonal_adjusted",
        ]
    ]


def main():

    print("🌱 Starting MetricPulse seasonal analysis...")

    df = pd.read_csv(INPUT_PATH)

    df["date"] = pd.to_datetime(df["date"])

    print(
        f"📊 Loaded {len(df):,} observations"
    )

    results = []

    for _, group in df.groupby(
        ["metric", "dimension", "segment"]
    ):

        result = analyze_series(group)

        if result is not None:
            results.append(result)

    if not results:
        raise ValueError(
            "No time series were long enough "
            "for seasonal decomposition."
        )

    seasonal = pd.concat(
        results,
        ignore_index=True
    )

    seasonal = seasonal.sort_values(
        [
            "date",
            "metric",
            "dimension",
            "segment",
        ]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    seasonal.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"✅ Created {len(seasonal):,} seasonal observations"
    )

    print(
        f"💾 Saved to {OUTPUT_PATH}"
    )

    print(
        "\n📈 Series analyzed:"
    )

    print(
        seasonal.groupby(
            ["metric", "dimension"]
        )
        .size()
    )

    print(
        "\n🎯 MetricPulse seasonal analysis complete!"
    )


if __name__ == "__main__":
    main()