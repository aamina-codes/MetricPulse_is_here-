import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ============================================================
# Anomaly windows
# ============================================================

ANDROID_ACTIVATION_ANOMALY_START = 50

PAID_SOCIAL_CONVERSION_ANOMALY_START = 65

INDIA_CONVERSION_ANOMALY_START = 75

# ============================================================
# Configuration
# ============================================================

NUM_USERS = 5_000
NUM_DAYS = 90

START_DATE = date(2026, 6, 1)

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ============================================================
# User dimensions
# ============================================================

PLATFORMS = {
    "Web": 0.40,
    "Android": 0.35,
    "iOS": 0.25,
}

REGIONS = {
    "North America": 0.30,
    "Europe": 0.25,
    "Asia": 0.25,
    "India": 0.20,
}

ACQUISITION_CHANNELS = {
    "Organic": 0.30,
    "Paid Search": 0.25,
    "Paid Social": 0.20,
    "Referral": 0.15,
    "Email": 0.10,
}


# ============================================================
# Baseline KPI probabilities
# ============================================================

BASE_ACTIVATION_RATE = 0.35
BASE_CONVERSION_RATE = 0.08

EVENT_TYPES = [
    "signup",
    "login",
    "activation",
    "purchase",
]


# ============================================================
# Helper functions
# ============================================================

def choose_weighted(options):
    """Choose one value using the supplied probability distribution."""
    return random.choices(
        list(options.keys()),
        weights=list(options.values()),
        k=1,
    )[0]


def get_activation_probability(platform, event_day):
    """
    Return activation probability based on the calendar day.

    Android activation experiences a sustained decline
    beginning on Day 50.
    """

    platform_adjustment = {
        "Web": 0.02,
        "iOS": 0.04,
        "Android": -0.04,
    }

    probability = BASE_ACTIVATION_RATE + platform_adjustment[platform]

    if (
        event_day >= ANDROID_ACTIVATION_ANOMALY_START
        and platform == "Android"
    ):
        probability -= 0.11

    return max(0.01, probability)

def get_conversion_probability(
    acquisition_channel,
    region,
    event_day,
):
    """
    Return purchase probability based on the calendar day.

    Two sustained anomalies are introduced:
    1. Paid Social conversion drops around Day 65.
    2. India conversion drops around Day 75.
    """

    channel_adjustment = {
        "Organic": 0.01,
        "Paid Search": 0.00,
        "Paid Social": -0.01,
        "Referral": 0.02,
        "Email": 0.00,
    }

    probability = (
        BASE_CONVERSION_RATE
        + channel_adjustment[acquisition_channel]
    )

    if (
        event_day >= PAID_SOCIAL_CONVERSION_ANOMALY_START
        and acquisition_channel == "Paid Social"
    ):
        probability -= 0.035

    if (
        event_day >= INDIA_CONVERSION_ANOMALY_START
        and region == "India"
    ):
        probability -= 0.04

    return max(0.005, probability)


def generate_login_dates(
    signup_date,
    num_days_after_signup,
):
    """
    Generate realistic return visits after signup.

    Users have a higher probability of returning shortly
    after signup, with activity gradually declining.
    """

    login_dates = []

    for day_offset in range(1, num_days_after_signup + 1):

        # Higher activity immediately after signup.
        if day_offset <= 7:
            probability = 0.45
        elif day_offset <= 30:
            probability = 0.20
        else:
            probability = 0.08

        if random.random() < probability:
            login_dates.append(
                signup_date + timedelta(days=day_offset)
            )

    return login_dates


# ============================================================
# Generate users
# ============================================================

def generate_users():

    users = []

    for user_id in range(1, NUM_USERS + 1):

        signup_offset = random.randint(0, NUM_DAYS - 1)

        signup_date = START_DATE + timedelta(
            days=signup_offset
        )

        platform = choose_weighted(PLATFORMS)
        region = choose_weighted(REGIONS)
        acquisition_channel = choose_weighted(
            ACQUISITION_CHANNELS
        )

        users.append(
            {
                "user_id": user_id,
                "signup_date": signup_date,
                "platform": platform,
                "region": region,
                "acquisition_channel": acquisition_channel,
            }
        )

    return pd.DataFrame(users)


# ============================================================
# Generate events
# ============================================================

def generate_events(users):

    events = []

    event_id = 1

    dataset_end_date = (
        START_DATE + timedelta(days=NUM_DAYS - 1)
    )

    for user in users.itertuples(index=False):

        user_id = user.user_id
        signup_date = user.signup_date

        days_remaining = (
            dataset_end_date - signup_date
        ).days

        # ----------------------------------------------------
        # Signup event
        # ----------------------------------------------------

        events.append(
            {
                "event_id": event_id,
                "user_id": user_id,
                "event_date": signup_date,
                "event_type": "signup",
            }
        )

        event_id += 1

        # ----------------------------------------------------
        # Activation
        # ----------------------------------------------------

        activation_delay = random.randint(0, 3)

        activation_date = (
            signup_date
            + timedelta(days=activation_delay)
        )

        if activation_date <= dataset_end_date:

            # Determine the calendar day of the activation.
            event_day = (
                activation_date - START_DATE
            ).days

            activation_probability = (
                get_activation_probability(
                    user.platform,
                    event_day,
                )
            )

            activated = (
                random.random()
                < activation_probability
            )

            if activated:

                events.append(
                    {
                        "event_id": event_id,
                        "user_id": user_id,
                        "event_date": activation_date,
                        "event_type": "activation",
                    }
                )

                event_id += 1

        # ----------------------------------------------------
        # Purchase
        # ----------------------------------------------------

        purchase_delay = random.randint(1, 14)

        purchase_date = (
            signup_date
            + timedelta(days=purchase_delay)
        )

        if purchase_date <= dataset_end_date:

            # Determine the calendar day of the purchase.
            event_day = (
                purchase_date - START_DATE
            ).days

            conversion_probability = (
                get_conversion_probability(
                    user.acquisition_channel,
                    user.region,
                    event_day,
                )
            )

            purchased = (
                random.random()
                < conversion_probability
            )

            if purchased:

                events.append(
                    {
                        "event_id": event_id,
                        "user_id": user_id,
                        "event_date": purchase_date,
                        "event_type": "purchase",
                    }
                )

                event_id += 1

        # ----------------------------------------------------
        # Login / retention activity
        # ----------------------------------------------------

        login_dates = generate_login_dates(
            signup_date,
            days_remaining,
        )

        for login_date in login_dates:

            events.append(
                {
                    "event_id": event_id,
                    "user_id": user_id,
                    "event_date": login_date,
                    "event_type": "login",
                }
            )

            event_id += 1

    return pd.DataFrame(events)
# ============================================================
# Main
# ============================================================

def main():

    print("🚀 Starting MetricPulse data generation...")

    print("\n👥 Generating users...")

    users = generate_users()

    print(f"Generated {len(users):,} users.")

    print("\n📊 Generating product events...")

    events = generate_events(users)

    print(f"Generated {len(events):,} events.")

    # --------------------------------------------------------
    # Save datasets
    # --------------------------------------------------------

    users.to_csv(
        "data/raw/users.csv",
        index=False,
    )

    events.to_csv(
        "data/raw/events.csv",
        index=False,
    )

    print("\n💾 Saved datasets:")
    print("   data/raw/users.csv")
    print("   data/raw/events.csv")

    # --------------------------------------------------------
    # Basic summary
    # --------------------------------------------------------

    print("\n📈 Event distribution:")

    print(
        events["event_type"]
        .value_counts()
        .to_string()
    )

    print("\n📱 Platform distribution:")

    print(
        users["platform"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
        .astype(str)
        .add("%")
        .to_string()
    )

    print("\n🌍 Region distribution:")

    print(
        users["region"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
        .astype(str)
        .add("%")
        .to_string()
    )

    print("\n✅ MetricPulse dataset generation complete!")


if __name__ == "__main__":
    main()