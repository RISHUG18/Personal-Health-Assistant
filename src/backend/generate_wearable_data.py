#!/usr/bin/env python3
"""
Wearable Data Generator
Generates 7 days of realistic minute-by-minute heart rate and sleep data.
Output: JSON payload for testing ingestion API (Person 3).
"""

import json
import random
from datetime import datetime, timedelta

def generate_heart_rate_data(start_date, days=7):
    """Generate minute-by-minute heart rate data."""
    data = []
    current = start_date
    end = start_date + timedelta(days=days)

    while current < end:
        # Base heart rate varies by time of day
        hour = current.hour
        if 6 <= hour < 12:  # Morning
            base_hr = random.randint(60, 75)
        elif 12 <= hour < 18:  # Afternoon
            base_hr = random.randint(70, 85)
        elif 18 <= hour < 22:  # Evening
            base_hr = random.randint(75, 90)
        else:  # Night
            base_hr = random.randint(55, 70)

        # Add some variability
        hr = base_hr + random.randint(-5, 5)
        hr = max(50, min(120, hr))  # Clamp to realistic range

        data.append({
            "timestamp": current.isoformat() + "Z",
            "heart_rate": hr,
            "source": "wearable"
        })

        current += timedelta(minutes=1)

    return data

def generate_sleep_data(start_date, days=7):
    """Generate sleep sessions (simplified to daily totals)."""
    data = []
    current = start_date

    for _ in range(days):
        # Sleep start around 11 PM, duration 6-9 hours
        sleep_start = current.replace(hour=23, minute=0, second=0)
        sleep_duration_hours = random.uniform(6, 9)
        sleep_end = sleep_start + timedelta(hours=sleep_duration_hours)

        # Sleep stages (simplified)
        stages = {
            "deep": sleep_duration_hours * 0.2,
            "light": sleep_duration_hours * 0.5,
            "rem": sleep_duration_hours * 0.25,
            "awake": sleep_duration_hours * 0.05
        }

        data.append({
            "date": current.date().isoformat(),
            "sleep_start": sleep_start.isoformat() + "Z",
            "sleep_end": sleep_end.isoformat() + "Z",
            "total_duration_hours": round(sleep_duration_hours, 2),
            "stages_hours": {k: round(v, 2) for k, v in stages.items()},
            "quality_score": random.randint(60, 95)  # Out of 100
        })

        current += timedelta(days=1)

    return data

def main():
    # Start from 7 days ago
    start_date = datetime.now() - timedelta(days=7)

    payload = {
        "patient_id": "pat-1",
        "data_type": "wearable",
        "generated_at": datetime.now().isoformat() + "Z",
        "heart_rate": generate_heart_rate_data(start_date),
        "sleep": generate_sleep_data(start_date)
    }

    # Output to stdout (can be redirected to file)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()