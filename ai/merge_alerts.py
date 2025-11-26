# ai/merge_alerts.py

import pandas as pd
from pathlib import Path
from config import DATA_DIR, SAMPLE_LOGS_ENRICHED_ML, SAMPLE_ALERTS_SEVERITY

def compute_severity(row):
    risk_level = row.get("risk_level", "low")
    ml_anom = row.get("ml_is_anomaly", 0)

    if risk_level == "high" and ml_anom == 1:
        return "critical"
    elif risk_level in ("medium", "high") or ml_anom == 1:
        return "medium"
    else:
        return "low"

def main():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SAMPLE_LOGS_ENRICHED_ML)
    print(f"[MERGE] Loaded {len(df)} ML-enriched events")

    df["alert_severity"] = df.apply(compute_severity, axis=1)

    # tu peux ajouter un champ "is_alert" si tu veux filtrer
    df["is_alert"] = df["alert_severity"].isin(["medium", "critical"]).astype(int)

    df.to_csv(SAMPLE_ALERTS_SEVERITY, index=False)
    print(f"[MERGE] Saved alerts with severity to {SAMPLE_ALERTS_SEVERITY}")

if __name__ == "__main__":
    main()
