-- ============================================
-- MetricPulse Database Schema
-- Product Analytics & Anomaly Detection
-- ============================================

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    signup_date DATE NOT NULL,

    platform VARCHAR(20) NOT NULL
        CHECK (platform IN ('Web', 'iOS', 'Android')),

    region VARCHAR(50) NOT NULL
        CHECK (region IN (
            'North America',
            'Europe',
            'Asia',
            'India'
        )),

    acquisition_channel VARCHAR(50) NOT NULL
        CHECK (acquisition_channel IN (
            'Organic',
            'Paid Search',
            'Paid Social',
            'Referral',
            'Email'
        ))
);


CREATE TABLE events (
    event_id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,

    event_date DATE NOT NULL,

    event_type VARCHAR(30) NOT NULL
        CHECK (event_type IN (
            'signup',
            'login',
            'activation',
            'purchase'
        )),

    CONSTRAINT fk_events_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
);


-- ============================================
-- Indexes
-- ============================================

CREATE INDEX idx_events_user_id
    ON events(user_id);

CREATE INDEX idx_events_date
    ON events(event_date);

CREATE INDEX idx_events_type
    ON events(event_type);

CREATE INDEX idx_users_signup_date
    ON users(signup_date);

CREATE INDEX idx_users_platform
    ON users(platform);

CREATE INDEX idx_users_region
    ON users(region);

CREATE INDEX idx_users_acquisition
    ON users(acquisition_channel);