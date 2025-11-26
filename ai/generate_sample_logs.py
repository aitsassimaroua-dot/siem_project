# ai/generate_sample_logs.py

import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
from config import DATA_DIR, SAMPLE_LOGS

USERS = [
    {"username": "alice", "role": "user"},
    {"username": "bob", "role": "user"},
    {"username": "charlie", "role": "user"},
    {"username": "admin", "role": "admin"},
]

INTERNAL_IPS = [
    "192.168.1.10",
    "192.168.1.11",
    "192.168.1.12",
    "10.0.0.5",
    "10.0.0.6",
]

EXTERNAL_IPS = [
    "203.0.113.10",
    "198.51.100.3",
    "8.8.8.8",
    "1.1.1.1",
    "51.89.23.14",
]

def random_timestamp_last_days(days=7):
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return now - delta

def generate_logs(n_events=1000, filename=SAMPLE_LOGS):
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    rows = []

    for _ in range(n_events):
        user_info = random.choice(USERS)
        user = user_info["username"]
        role = user_info["role"]

        ts = random_timestamp_last_days()
        hour = ts.hour
        weekday = ts.weekday()

        # 80% internes, 20% externes
        ip = random.choice(INTERNAL_IPS) if random.random() < 0.8 else random.choice(EXTERNAL_IPS)

        # prob d'échec différente pour admin
        fail_prob = 0.15 if role == "admin" else 0.05

        if random.random() < 0.05:
            status = "FAIL"
            reason = "bad_password"
        else:
            if random.random() < fail_prob:
                status = "FAIL"
                reason = random.choice(["bad_password", "unknown_user"])
            else:
                status = "SUCCESS"
                reason = "ok"

        rows.append({
            "timestamp": ts.isoformat(timespec="seconds"),
            "user": user,
            "role": role,
            "ip": ip,
            "status": status,
            "reason": reason,
            "hour": hour,
            "weekday": weekday,
        })

    # petites séries ciblées sur admin
    for _ in range(30):
        ts = random_timestamp_last_days()
        rows.append({
            "timestamp": ts.isoformat(timespec="seconds"),
            "user": "admin",
            "role": "admin",
            "ip": random.choice(EXTERNAL_IPS),
            "status": "FAIL",
            "reason": "bad_password",
            "hour": ts.hour,
            "weekday": ts.weekday(),
        })

    fieldnames = ["timestamp", "user", "role", "ip", "status", "reason", "hour", "weekday"]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[generate_sample_logs] Generated {len(rows)} events in {filename}")

if __name__ == "__main__":
    generate_logs()
