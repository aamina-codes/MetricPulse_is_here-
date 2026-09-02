import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = Path(
    "data/processed/metric_observations.csv"
)

OUTPUT_PATH = Path(
    "data/processed/change_points.csv"
)


# ============================================================
# DETECTION PARAMETERS
# ============================================================

# Minimum number of observations required for a time series.
MIN_OBSERVATIONS = 21

# Ignore observations based on extremely small sample sizes.
MIN_SAMPLE_SIZE = 10

# Number of historical observations used for the baseline.
BASELINE_WINDOW = 14

# Minimum number of historical observations needed.
MIN_BASELINE_POINTS = 7

# CUSUM threshold required before a shift can be considered.
CHANGE_THRESHOLD = 4.5

# Minimum relative movement from baseline.
MIN_SHIFT_RATIO = 0.15

# Minimum absolute percentage-point movement.
#
# This prevents very small metrics from generating
# large relative changes from tiny baselines.
MIN_ABSOLUTE_SHIFT = 0.02

# Number of consecutive observations required to
# confirm a sustained directional movement.
SUSTAINED_POINTS = 2

# Minimum number of days between detected change points
# for the same metric / dimension / segment.
COOLDOWN_DAYS = 7


# ============================================================
# HELPERS
# ============================================================

def calculate_confidence(
    shift_ratio,
    cusum_score,
    sample_size
):
    """
    Assign confidence based on:

    1. Magnitude of movement
    2. CUSUM strength
    3. Sample size
    """

    score = 0

    # --------------------------------------------------------
    # Magnitude
    # --------------------------------------------------------

    if shift_ratio >= 0.50:
        score += 2

    elif shift_ratio >= 0.30:
        score += 1

    # --------------------------------------------------------
    # CUSUM strength
    # --------------------------------------------------------

    if cusum_score >= 8:
        score += 2

    elif cusum_score >= 5:
        score += 1

    # --------------------------------------------------------
    # Sample size
    # --------------------------------------------------------

    if sample_size >= 25:
        score += 2

    elif sample_size >= 15:
        score += 1

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if score >= 5:
        return "high"

    return "medium"


# ============================================================
# CHANGE-POINT DETECTION
# ============================================================

def detect_change_points(group):
    """
    Detect sustained directional shifts in a single
    metric / dimension / segment time series.

    Detection combines:

    - Historical rolling baseline
    - Standardized deviation
    - CUSUM-style accumulation
    - Relative shift threshold
    - Absolute movement threshold
    - Sample-size protection
    - Sustained movement confirmation
    - Cooldown period
    """

    group = (
        group
        .sort_values("date")
        .copy()
    )

    # --------------------------------------------------------
    # Validate time-series length
    # --------------------------------------------------------

    if len(group) < MIN_OBSERVATIONS:
        return None

    values = (
        group["value"]
        .astype(float)
        .to_numpy()
    )

    dates = (
        pd.to_datetime(
            group["date"]
        )
        .to_numpy()
    )

    sample_sizes = (
        group["sample_size"]
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    # --------------------------------------------------------
    # Result structure
    # --------------------------------------------------------

    result = group[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ].copy()

    result["baseline"] = np.nan
    result["shift_ratio"] = np.nan
    result["shift_pct"] = np.nan

    result["cusum_positive"] = 0.0
    result["cusum_negative"] = 0.0

    result["change_direction"] = "none"
    result["confidence"] = "none"
    result["is_change_point"] = False

    # --------------------------------------------------------
    # CUSUM state
    # --------------------------------------------------------

    positive_sum = 0.0
    negative_sum = 0.0

    # ========================================================
    # HISTORICAL BASELINE + CUSUM
    # ========================================================

    for i in range(len(values)):

        # Need enough historical data.
        if i < MIN_BASELINE_POINTS:
            continue

        start = max(
            0,
            i - BASELINE_WINDOW
        )

        historical_values = values[start:i]

        if (
            len(historical_values)
            < MIN_BASELINE_POINTS
        ):
            continue

        baseline = np.mean(
            historical_values
        )

        baseline_std = np.std(
            historical_values,
            ddof=1
        )

        if np.isnan(baseline_std):
            continue

        # ----------------------------------------------------
        # Protect against zero / extremely small variance.
        # ----------------------------------------------------

        scale = max(
            baseline_std,
            0.01
        )

        deviation = (
            values[i] - baseline
        ) / scale

        # ----------------------------------------------------
        # Relative shift
        # ----------------------------------------------------

        if abs(baseline) > 1e-9:

            shift_ratio = (
                abs(values[i] - baseline)
                / abs(baseline)
            )

        else:

            shift_ratio = np.nan

        # ----------------------------------------------------
        # Relative percentage shift
        #
        # Example:
        # baseline = 0.10
        # value    = 0.05
        #
        # shift_pct = -50%
        # ----------------------------------------------------

        if abs(baseline) > 1e-9:

            shift_pct = (
                (values[i] - baseline)
                / abs(baseline)
            ) * 100

        else:

            shift_pct = np.nan

        # ----------------------------------------------------
        # Store baseline information
        # ----------------------------------------------------

        result.loc[
            result.index[i],
            "baseline"
        ] = baseline

        result.loc[
            result.index[i],
            "shift_ratio"
        ] = shift_ratio

        result.loc[
            result.index[i],
            "shift_pct"
        ] = shift_pct

        # ====================================================
        # CUSUM
        # ====================================================

        positive_sum = max(
            0,
            positive_sum + deviation
        )

        negative_sum = min(
            0,
            negative_sum + deviation
        )

        result.loc[
            result.index[i],
            "cusum_positive"
        ] = positive_sum

        result.loc[
            result.index[i],
            "cusum_negative"
        ] = negative_sum

    # ========================================================
    # RAW CANDIDATES
    # ========================================================

    candidate_indices = []

    for i in range(len(result)):

        baseline = result.iloc[i]["baseline"]

        shift_ratio = result.iloc[i]["shift_ratio"]

        sample_size = sample_sizes[i]

        if pd.isna(baseline):
            continue

        if pd.isna(shift_ratio):
            continue

        # ----------------------------------------------------
        # Sample-size protection
        # ----------------------------------------------------

        if sample_size < MIN_SAMPLE_SIZE:
            continue

        # ----------------------------------------------------
        # Relative movement protection
        # ----------------------------------------------------

        if shift_ratio < MIN_SHIFT_RATIO:
            continue

        # ----------------------------------------------------
        # Absolute movement protection
        #
        # Example:
        # 1% -> 1.2%
        #
        # Relative change = 20%
        #
        # But absolute movement = only 0.2 percentage points.
        #
        # This should NOT automatically become a meaningful
        # business change point.
        # ----------------------------------------------------

        absolute_shift = abs(
            values[i] - baseline
        )

        if absolute_shift < MIN_ABSOLUTE_SHIFT:
            continue

        positive = result.iloc[i][
            "cusum_positive"
        ]

        negative = result.iloc[i][
            "cusum_negative"
        ]

        direction = None

        # ----------------------------------------------------
        # Direction detection
        # ----------------------------------------------------

        if positive >= CHANGE_THRESHOLD:

            direction = "increase"

        elif negative <= -CHANGE_THRESHOLD:

            direction = "decrease"

        if direction is None:
            continue

        candidate_indices.append(
            (i, direction)
        )

    # ========================================================
    # SUSTAINED MOVEMENT CONFIRMATION
    # ========================================================

    sustained_candidates = []

    for i, direction in candidate_indices:

        future_end = min(
            len(result),
            i + SUSTAINED_POINTS
        )

        future_values = values[
            i:future_end
        ]

        baseline = result.iloc[i][
            "baseline"
        ]

        if pd.isna(baseline):
            continue

        # Need the complete confirmation window.
        if len(future_values) < SUSTAINED_POINTS:
            continue

        # ----------------------------------------------------
        # Increase
        # ----------------------------------------------------

        if direction == "increase":

            sustained = all(
                value > baseline
                for value in future_values
            )

        # ----------------------------------------------------
        # Decrease
        # ----------------------------------------------------

        else:

            sustained = all(
                value < baseline
                for value in future_values
            )

        if sustained:

            sustained_candidates.append(
                (i, direction)
            )

    # ========================================================
    # COOLDOWN
    # ========================================================

    last_change_date = None

    for i, direction in sustained_candidates:

        current_date = pd.Timestamp(
            dates[i]
        )

        # ----------------------------------------------------
        # Prevent multiple alerts in a short period.
        # ----------------------------------------------------

        if last_change_date is not None:

            days_since_last_change = (
                current_date -
                last_change_date
            ).days

            if (
                days_since_last_change
                < COOLDOWN_DAYS
            ):
                continue

        baseline = result.iloc[i][
            "baseline"
        ]

        shift_ratio = result.iloc[i][
            "shift_ratio"
        ]

        positive = result.iloc[i][
            "cusum_positive"
        ]

        negative = result.iloc[i][
            "cusum_negative"
        ]

        # ----------------------------------------------------
        # Direction-specific CUSUM score
        # ----------------------------------------------------

        cusum_score = (
            positive
            if direction == "increase"
            else abs(negative)
        )

        sample_size = sample_sizes[i]

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        confidence = calculate_confidence(
            shift_ratio,
            cusum_score,
            sample_size
        )

        # ----------------------------------------------------
        # Store detection
        # ----------------------------------------------------

        result.loc[
            result.index[i],
            "change_direction"
        ] = direction

        result.loc[
            result.index[i],
            "confidence"
        ] = confidence

        result.loc[
            result.index[i],
            "is_change_point"
        ] = True

        last_change_date = current_date

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "🔎 Starting MetricPulse change-point detection..."
    )

    # ========================================================
    # LOAD OBSERVATIONS
    # ========================================================

    df = pd.read_csv(
        INPUT_PATH
    )

    df["date"] = pd.to_datetime(
        df["date"]
    )

    print(
        f"📊 Loaded {len(df):,} observations"
    )

    # ========================================================
    # VALIDATE REQUIRED COLUMNS
    # ========================================================

    required_columns = {
        "date",
        "metric",
        "dimension",
        "segment",
        "value",
        "sample_size",
    }

    missing_columns = (
        required_columns -
        set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    # ========================================================
    # DETECT CHANGE POINTS
    # ========================================================

    results = []

    grouped = df.groupby(
        [
            "metric",
            "dimension",
            "segment",
        ]
    )

    for _, group in grouped:

        result = detect_change_points(
            group
        )

        if result is not None:

            results.append(
                result
            )

    if not results:

        raise ValueError(
            "No time series were long enough "
            "for change-point detection."
        )

    change_points = pd.concat(
        results,
        ignore_index=True
    )

    # ========================================================
    # CLEAN + SORT
    # ========================================================

    change_points = (
        change_points
        .sort_values(
            [
                "date",
                "metric",
                "dimension",
                "segment",
            ]
        )
        .reset_index(drop=True)
    )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    change_points.to_csv(
        OUTPUT_PATH,
        index=False
    )

    detected = change_points[
        change_points["is_change_point"]
    ].copy()

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"💾 Saved results to {OUTPUT_PATH}"
    )

    print(
        f"\n🚨 {len(detected):,} meaningful "
        f"change points detected"
    )

    if not detected.empty:

        print(
            "\nChange-point summary:\n"
        )

        summary_columns = [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "baseline",
            "shift_pct",
            "sample_size",
            "change_direction",
            "confidence",
            "cusum_positive",
            "cusum_negative",
        ]

        # ----------------------------------------------------
        # Round ONLY numeric columns.
        #
        # This removes the pandas datetime warning.
        # ----------------------------------------------------

        summary = detected[
            summary_columns
        ].copy()

        numeric_columns = [
            "value",
            "baseline",
            "shift_pct",
            "cusum_positive",
            "cusum_negative",
        ]

        summary[
            numeric_columns
        ] = summary[
            numeric_columns
        ].round(4)

        print(
            summary.to_string(
                index=False
            )
        )

        # ====================================================
        # METRIC SUMMARY
        # ====================================================

        print(
            "\n📈 Change points by metric:"
        )

        print(
            detected
            .groupby("metric")
            .size()
        )

        # ====================================================
        # DIRECTION SUMMARY
        # ====================================================

        print(
            "\n📊 Change points by direction:"
        )

        print(
            detected
            .groupby("change_direction")
            .size()
        )

        # ====================================================
        # CONFIDENCE SUMMARY
        # ====================================================

        print(
            "\n🎯 Change points by confidence:"
        )

        print(
            detected
            .groupby("confidence")
            .size()
        )

        # ====================================================
        # DIMENSION SUMMARY
        # ====================================================

        print(
            "\n📋 Change points by dimension:"
        )

        print(
            detected
            .groupby("dimension")
            .size()
        )

    else:

        print(
            "\nℹ️ No meaningful change points detected."
        )

    print(
        "\n🎯 MetricPulse change-point "
        "detection complete!"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()