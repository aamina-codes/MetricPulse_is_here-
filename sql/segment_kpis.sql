-- ============================================================
-- MetricPulse Segment KPIs
-- ============================================================

-- ============================================================
-- 1. 7-Day Activation Rate by Platform
-- ============================================================

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
),

activation_cohorts AS (

    SELECT
        signup_date,
        platform,

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

    GROUP BY
        signup_date,
        platform
)

SELECT
    signup_date,
    platform,
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

ORDER BY
    signup_date,
    platform;


-- ============================================================
-- 2. 14-Day Conversion Rate by Region
-- ============================================================

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
),

conversion_cohorts AS (

    SELECT
        signup_date,
        region,

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

    GROUP BY
        signup_date,
        region
)

SELECT
    signup_date,
    region,
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

ORDER BY
    signup_date,
    region;

-- ============================================================
-- 3. 14-Day Conversion Rate by Acquisition Channel
-- ============================================================

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
),

conversion_cohorts AS (

    SELECT
        signup_date,
        acquisition_channel,

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

    GROUP BY
        signup_date,
        acquisition_channel
)

SELECT
    signup_date,
    acquisition_channel,
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

ORDER BY
    signup_date,
    acquisition_channel;