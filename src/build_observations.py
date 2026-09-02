import pandas as pd
import psycopg2
from pathlib import Path


DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "metricpulse",
    "user": "metricpulse",
    "password": "metricpulse_dev",
}


OUTPUT_PATH = Path("data/processed/metric_observations.csv")


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def load_activation_by_platform(conn):
    query = """
        WITH user_activation AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.platform,
                MIN(e.event_date) AS activation_date
            FROM users u
            LEFT JOIN events e
                ON u.user_id = e.user_id
                AND e.event_type = 'activation'
            GROUP BY
                u.user_id,
                u.signup_date,
                u.platform
        )

        SELECT
            signup_date AS date,
            'activation' AS metric,
            'platform' AS dimension,
            platform AS segment,
            COUNT(*) AS sample_size,
            COUNT(
                CASE
                    WHEN activation_date IS NOT NULL
                    AND activation_date <=
                        signup_date + INTERVAL '7 days'
                    THEN 1
                END
            ) AS successes
        FROM user_activation
        GROUP BY
            signup_date,
            platform
        ORDER BY
            signup_date,
            platform;
    """

    df = pd.read_sql(query, conn)

    df["value"] = (
        df["successes"] / df["sample_size"]
    )

    return df[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ]


def load_conversion_by_region(conn):
    query = """
        WITH user_conversion AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.region,
                MIN(e.event_date) AS purchase_date
            FROM users u
            LEFT JOIN events e
                ON u.user_id = e.user_id
                AND e.event_type = 'purchase'
            GROUP BY
                u.user_id,
                u.signup_date,
                u.region
        )

        SELECT
            signup_date AS date,
            'conversion' AS metric,
            'region' AS dimension,
            region AS segment,
            COUNT(*) AS sample_size,
            COUNT(
                CASE
                    WHEN purchase_date IS NOT NULL
                    AND purchase_date <=
                        signup_date + INTERVAL '14 days'
                    THEN 1
                END
            ) AS successes
        FROM user_conversion
        GROUP BY
            signup_date,
            region
        ORDER BY
            signup_date,
            region;
    """

    df = pd.read_sql(query, conn)

    df["value"] = (
        df["successes"] / df["sample_size"]
    )

    return df[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ]


def load_conversion_by_channel(conn):
    query = """
        WITH user_conversion AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.acquisition_channel,
                MIN(e.event_date) AS purchase_date
            FROM users u
            LEFT JOIN events e
                ON u.user_id = e.user_id
                AND e.event_type = 'purchase'
            GROUP BY
                u.user_id,
                u.signup_date,
                u.acquisition_channel
        )

        SELECT
            signup_date AS date,
            'conversion' AS metric,
            'channel' AS dimension,
            acquisition_channel AS segment,
            COUNT(*) AS sample_size,
            COUNT(
                CASE
                    WHEN purchase_date IS NOT NULL
                    AND purchase_date <=
                        signup_date + INTERVAL '14 days'
                    THEN 1
                END
            ) AS successes
        FROM user_conversion
        GROUP BY
            signup_date,
            acquisition_channel
        ORDER BY
            signup_date,
            acquisition_channel;
    """

    df = pd.read_sql(query, conn)

    df["value"] = (
        df["successes"] / df["sample_size"]
    )

    return df[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ]

def load_retention_by_platform(conn):
    query = """
        WITH user_retention AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.platform,
                MAX(
                    CASE
                        WHEN e.event_type = 'login'
                        AND e.event_date > u.signup_date
                        AND e.event_date <=
                            u.signup_date + INTERVAL '7 days'
                        THEN 1
                        ELSE 0
                    END
                ) AS retained
            FROM users u
            LEFT JOIN events e
                ON u.user_id = e.user_id
            GROUP BY
                u.user_id,
                u.signup_date,
                u.platform
        )

        SELECT
            signup_date AS date,
            'retention' AS metric,
            'platform' AS dimension,
            platform AS segment,
            COUNT(*) AS sample_size,
            SUM(retained) AS successes
        FROM user_retention
        GROUP BY
            signup_date,
            platform
        ORDER BY
            signup_date,
            platform;
    """

    df = pd.read_sql(query, conn)

    df["value"] = (
        df["successes"] / df["sample_size"]
    )

    return df[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ]


def load_retention_by_region(conn):
    query = """
        WITH user_retention AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.region,
                MAX(
                    CASE
                        WHEN e.event_type = 'login'
                        AND e.event_date > u.signup_date
                        AND e.event_date <=
                            u.signup_date + INTERVAL '7 days'
                        THEN 1
                        ELSE 0
                    END
                ) AS retained
            FROM users u
            LEFT JOIN events e
                ON u.user_id = e.user_id
            GROUP BY
                u.user_id,
                u.signup_date,
                u.region
        )

        SELECT
            signup_date AS date,
            'retention' AS metric,
            'region' AS dimension,
            region AS segment,
            COUNT(*) AS sample_size,
            SUM(retained) AS successes
        FROM user_retention
        GROUP BY
            signup_date,
            region
        ORDER BY
            signup_date,
            region;
    """

    df = pd.read_sql(query, conn)

    df["value"] = (
        df["successes"] / df["sample_size"]
    )

    return df[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ]


def load_retention_by_channel(conn):
    query = """
        WITH user_retention AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.acquisition_channel,
                MAX(
                    CASE
                        WHEN e.event_type = 'login'
                        AND e.event_date > u.signup_date
                        AND e.event_date <=
                            u.signup_date + INTERVAL '7 days'
                        THEN 1
                        ELSE 0
                    END
                ) AS retained
            FROM users u
            LEFT JOIN events e
                ON u.user_id = e.user_id
            GROUP BY
                u.user_id,
                u.signup_date,
                u.acquisition_channel
        )

        SELECT
            signup_date AS date,
            'retention' AS metric,
            'channel' AS dimension,
            acquisition_channel AS segment,
            COUNT(*) AS sample_size,
            SUM(retained) AS successes
        FROM user_retention
        GROUP BY
            signup_date,
            acquisition_channel
        ORDER BY
            signup_date,
            acquisition_channel;
    """

    df = pd.read_sql(query, conn)

    df["value"] = (
        df["successes"] / df["sample_size"]
    )

    return df[
        [
            "date",
            "metric",
            "dimension",
            "segment",
            "value",
            "sample_size",
        ]
    ]

def main():
    MIN_SAMPLE_SIZE = 10

    print("🚀 Building MetricPulse observation layer...")

    conn = get_connection()

    try:
        platform = load_activation_by_platform(conn)
        region = load_conversion_by_region(conn)
        channel = load_conversion_by_channel(conn)
        retention_platform = load_retention_by_platform(conn)
        retention_region = load_retention_by_region(conn)
        retention_channel = load_retention_by_channel(conn)

    finally:
        conn.close()

    observations = pd.concat(
    [
        platform,
        region,
        channel,
        retention_platform,
        retention_region,
        retention_channel,
    ],
    ignore_index=True,
)
    observations = observations[
        observations["sample_size"] >= MIN_SAMPLE_SIZE
    ].copy()

    observations["date"] = pd.to_datetime(
        observations["date"]
    ).dt.date

    observations = observations.sort_values(
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

    observations.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"✅ Created {len(observations):,} observations"
    )

    print(
        f"💾 Saved to {OUTPUT_PATH}"
    )

    print("\n📊 Observation distribution:")

    print(
        observations.groupby(
            ["metric", "dimension"]
        ).size()
    )


if __name__ == "__main__":
    main()