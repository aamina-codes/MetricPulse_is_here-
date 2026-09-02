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


DATA_PATH = Path("data/processed")


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def create_tables(conn):
    cursor = conn.cursor()

    print("🏗️ Creating analytics tables...")

    # Drop only the analytics tables.
    # Raw users/events remain untouched.
    cursor.execute("DROP TABLE IF EXISTS anomalies;")
    cursor.execute("DROP TABLE IF EXISTS change_points;")
    cursor.execute("DROP TABLE IF EXISTS seasonal_analysis;")
    cursor.execute("DROP TABLE IF EXISTS insights;")

    cursor.execute("""
        CREATE TABLE anomalies (
            date DATE,
            metric TEXT,
            dimension TEXT,
            segment TEXT,
            value DOUBLE PRECISION,
            sample_size INTEGER,
            rolling_mean DOUBLE PRECISION,
            rolling_std DOUBLE PRECISION,
            z_score DOUBLE PRECISION,
            anomaly_direction TEXT,
            is_anomaly BOOLEAN,
            confidence TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE change_points (
            date DATE,
            metric TEXT,
            dimension TEXT,
            segment TEXT,
            value DOUBLE PRECISION,
            sample_size INTEGER,
            baseline DOUBLE PRECISION,
            shift_ratio DOUBLE PRECISION,
            shift_pct DOUBLE PRECISION,
            cusum_positive DOUBLE PRECISION,
            cusum_negative DOUBLE PRECISION,
            change_direction TEXT,
            confidence TEXT,
            is_change_point BOOLEAN
        );
    """)

    cursor.execute("""
        CREATE TABLE seasonal_analysis (
            date DATE,
            metric TEXT,
            dimension TEXT,
            segment TEXT,
            observed DOUBLE PRECISION,
            trend DOUBLE PRECISION,
            seasonal DOUBLE PRECISION,
            residual DOUBLE PRECISION,
            residual_z_score DOUBLE PRECISION,
            seasonal_adjusted DOUBLE PRECISION
        );
    """)

    cursor.execute("""
        CREATE TABLE insights (
            date DATE,
            metric TEXT,
            dimension TEXT,
            segment TEXT,
            insight_type TEXT,
            severity TEXT,
            priority TEXT,
            direction TEXT,
            interpretation TEXT,
            value DOUBLE PRECISION,
            baseline DOUBLE PRECISION,
            change_pct DOUBLE PRECISION,
            sample_size INTEGER,
            confidence TEXT,
            z_score DOUBLE PRECISION,
            recommendation TEXT,
            insight TEXT,
            seasonal DOUBLE PRECISION,
            seasonal_adjusted DOUBLE PRECISION,
            residual_z_score DOUBLE PRECISION,
            seasonality_context TEXT
        );
    """)

    conn.commit()
    cursor.close()

    print("✅ Analytics tables created.")


def prepare_dataframe(df):
    """Prepare dataframe values for PostgreSQL."""

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    # Convert NaN / NaT to None
    df = df.astype(object).where(pd.notnull(df), None)

    return df


def load_dataframe(conn, df, table_name):
    """Insert dataframe rows into PostgreSQL."""

    df = prepare_dataframe(df)

    columns = list(df.columns)

    column_sql = ", ".join(
        f'"{column}"'
        for column in columns
    )

    placeholders = ", ".join(
        ["%s"] * len(columns)
    )

    query = f"""
        INSERT INTO {table_name}
        ({column_sql})
        VALUES ({placeholders})
    """

    cursor = conn.cursor()

    rows = list(
        df.itertuples(
            index=False,
            name=None
        )
    )

    cursor.executemany(query, rows)

    conn.commit()
    cursor.close()

    print(
        f"   ✅ Loaded {len(df):,} rows → {table_name}"
    )


def load_csv(conn, filename, table_name):
    path = DATA_PATH / filename

    print(f"\n📂 Loading {filename}...")

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}"
        )

    df = pd.read_csv(path)

    print(
        f"   📊 CSV shape: {df.shape}"
    )

    load_dataframe(
        conn,
        df,
        table_name
    )


def main():

    print(
        "🚀 Loading MetricPulse analytics layer..."
    )

    conn = get_connection()

    try:

        create_tables(conn)

        load_csv(
            conn,
            "anomalies.csv",
            "anomalies"
        )

        load_csv(
            conn,
            "change_points.csv",
            "change_points"
        )

        load_csv(
            conn,
            "seasonal_analysis.csv",
            "seasonal_analysis"
        )

        load_csv(
            conn,
            "insights.csv",
            "insights"
        )

    finally:
        conn.close()

    print(
        "\n🎯 MetricPulse analytics layer "
        "loaded successfully!"
    )


if __name__ == "__main__":
    main()