# ai/ueba_risk_score.py

import pandas as pd
from pathlib import Path
from config import DATA_DIR, SAMPLE_LOGS, SAMPLE_LOGS_ENRICHED

def load_events_from_csv(path: str = SAMPLE_LOGS) -> pd.DataFrame:
    df = pd.read_csv(path)
    # parse timestamp si besoin
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def build_user_profiles(df: pd.DataFrame):
    """
    Profil simple par user:
    - plage horaire habituelle (hour_min / hour_max)
    - taux d'échec moyen (fail_rate)
    - IPs connues
    """
    profiles = {}
    for user, group in df.groupby("user"):
        hours = group["hour"].dropna()
        if len(hours) == 0:
            continue

        fail_rate = (group["status"] == "FAIL").mean()
        known_ips = set(group["ip"].unique())

        profiles[user] = {
            "hour_min": hours.quantile(0.1),
            "hour_max": hours.quantile(0.9),
            "fail_rate": fail_rate,
            "known_ips": known_ips,
        }
    return profiles

def compute_risk_for_event(event, profiles):
    user = event["user"]
    ip = event["ip"]
    hour = event["hour"]
    status = event["status"]
    role = event.get("role", "user")

    base_risk = 0
    profile = profiles.get(user)

    # Pas de profil → comportement inconnu → risque plus élevé
    if profile is None:
        base_risk += 40
    else:
        # 1) Horaire en dehors de l'habitude
        if hour < profile["hour_min"] or hour > profile["hour_max"]:
            base_risk += 25

        # 2) IP nouvelle pour ce user
        if ip not in profile["known_ips"]:
            base_risk += 25

        # 3) Echec inhabituel pour ce user
        if status == "FAIL" and profile["fail_rate"] < 0.1:
            base_risk += 20

    # 4) Admin → plus critique
    if role == "admin":
        base_risk += 20

    # 5) FAIL + IP externe → encore un peu plus
    if status == "FAIL" and not ip.startswith(("192.168.", "10.")):
        base_risk += 10

    # clamp
    base_risk = max(0, min(100, base_risk))

    if base_risk >= 70:
        level = "high"
    elif base_risk >= 40:
        level = "medium"
    else:
        level = "low"

    return base_risk, level

def enrich_with_risk(df: pd.DataFrame, profiles):
    risk_scores = []
    risk_levels = []
    for _, row in df.iterrows():
        risk, level = compute_risk_for_event(row, profiles)
        risk_scores.append(risk)
        risk_levels.append(level)
    df["risk_score"] = risk_scores
    df["risk_level"] = risk_levels
    return df

def main():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    df = load_events_from_csv()
    print(f"[UEBA] Loaded {len(df)} events")

    profiles = build_user_profiles(df)
    print(f"[UEBA] Built profiles for {len(profiles)} users")

    df_enriched = enrich_with_risk(df, profiles)
    df_enriched.to_csv(SAMPLE_LOGS_ENRICHED, index=False)
    print(f"[UEBA] Saved enriched events to {SAMPLE_LOGS_ENRICHED}")

if __name__ == "__main__":
    main()
