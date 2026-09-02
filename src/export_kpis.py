import pandas as pd
import psycopg2


# ============================================================
# PostgreSQL configuration
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "metricpulse",
    "user": "metricpulse",
    "password": "metricpulse_dev",
}


# ============================================================
# Queries
# ============================================================

ACTIVATION_QUERY = """
WITH user_activation AS (

    SELECT
        u.user_id,
        u.signup_date,
        MIN(e.event_date) AS activation_date

    FROM users u

    LEFT JOIN events e
        ON u.user_id = e.user_id
        AND e.event_type = 'activation'

    GROUP BY
        u.user_id,
        u.signup_date
),

activation_cohorts AS (

    SELECT
        signup_date,
        COUNT(*) AS new_users,

        COUNT(
            CASE
                WHEN activation_date IS NOT NULL
                AND activation_date <=
                    signup_date + INTERVAL '7 days'
                THEN 1
            END
        ) AS activated_users

    FROM user_activation

    GROUP BY signup_date
)

SELECT
    signup_date,
    new_users,
    activated_users,

    ROUND(
        activated_users::NUMERIC
        / NULLIF(new_users, 0),
        4
    ) AS activation_rate

FROM activation_cohorts

WHERE signup_date <= (
    SELECT MAX(event_date)::DATE
    FROM events
) - INTERVAL '7 days'

ORDER BY signup_date;
"""


CONVERSION_QUERY = """
WITH user_conversion AS (

    SELECT
        u.user_id,
        u.signup_date,
        MIN(e.event_date) AS purchase_date

    FROM users u

    LEFT JOIN events e
        ON u.user_id = e.user_id
        AND e.event_type = 'purchase'

    GROUP BY
        u.user_id,
        u.signup_date
),

conversion_cohorts AS (

    SELECT
        signup_date,
        COUNT(*) AS new_users,

        COUNT(
            CASE
                WHEN purchase_date IS NOT NULL
                AND purchase_date <=
                    signup_date + INTERVAL '14 days'
                THEN 1
            END
        ) AS converted_users

    FROM user_conversion

    GROUP BY signup_date
)

SELECT
    signup_date,
    new_users,
    converted_users,

    ROUND(
        converted_users::NUMERIC
        / NULLIF(new_users, 0),
        4
    ) AS conversion_rate

FROM conversion_cohorts

WHERE signup_date <= (
    SELECT MAX(event_date)::DATE
    FROM events
) - INTERVAL '14 days'

ORDER BY signup_date;
"""


RETENTION_QUERY = """
WITH user_retention AS (

    SELECT
        u.user_id,
        u.signup_date,
        COUNT(e.event_id) AS login_count

    FROM users u

    LEFT JOIN events e
        ON u.user_id = e.user_id
        AND e.event_type = 'login'
        AND e.event_date > u.signup_date
        AND e.event_date <=
            u.signup_date + INTERVAL '7 days'

    GROUP BY
        u.user_id,
        u.signup_date
),

retention_cohorts AS (

    SELECT
        signup_date,
        COUNT(*) AS new_users,

        COUNT(
            CASE
                WHEN login_count > 0
                THEN 1
            END
        ) AS retained_users

    FROM user_retention

    GROUP BY signup_date
)

SELECT
    signup_date,
    new_users,
    retained_users,

    ROUND(
        retained_users::NUMERIC
        / NULLIF(new_users, 0),
        4
    ) AS retention_rate

FROM retention_cohorts

WHERE signup_date <= (
    SELECT MAX(event_date)::DATE
    FROM events
) - INTERVAL '7 days'

ORDER BY signup_date;
"""


# ============================================================
# Main
# ============================================================

def main():

    print("📊 Exporting KPI data from PostgreSQL...")

    connection = psycopg2.connect(
        **DB_CONFIG
    )

    activation = pd.read_sql(
        ACTIVATION_QUERY,
        connection,
    )

    conversion = pd.read_sql(
        CONVERSION_QUERY,
        connection,
    )

    retention = pd.read_sql(
        RETENTION_QUERY,
        connection,
    )

    connection.close()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    activation.to_csv(
        "data/processed/activation_kpi.csv",
        index=False,
    )

    conversion.to_csv(
        "data/processed/conversion_kpi.csv",
        index=False,
    )

    retention.to_csv(
        "data/processed/retention_kpi.csv",
        index=False,
    )

    print(
        f"✅ Activation KPI: {len(activation)} rows"
    )

    print(
        f"✅ Conversion KPI: {len(conversion)} rows"
    )

    print(
        f"✅ Retention KPI: {len(retention)} rows"
    )

    print(
        "\n💾 Saved KPI datasets to "
        "data/processed/"
    )


if __name__ == "__main__":
    main()