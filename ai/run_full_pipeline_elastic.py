# ai/run_full_pipeline_elastic.py

import pandas as pd
from pathlib import Path

from config import (
    INDEX_SRC_CLEAN,
    INDEX_ENRICHED,
    INDEX_ALERTS_ENRICHED,
)
from elastic_client import fetch_index_as_dataframe, bulk_index
from ueba_risk_score import build_user_profiles, enrich_with_risk
from ml_anomaly import train_model, score_events
from merge_alerts import compute_severity


def run_pipeline_from_elastic():
    # 1) Lire les logs normalisés depuis Elasticsearch
    print(f"[PIPELINE] Fetching logs from index: {INDEX_SRC_CLEAN}")
    df = fetch_index_as_dataframe(INDEX_SRC_CLEAN, size=10000)

    if df.empty:
        print("[PIPELINE] No data found in auth-logs-clean. Aborting.")
        return

    # S'assurer que timestamp est bien parsé
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    elif "@timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["@timestamp"])
    else:
        print("[PIPELINE] No timestamp field found, expected 'timestamp' or '@timestamp'.")
        return

    print(f"[PIPELINE] Loaded {len(df)} events from Elasticsearch")

    # 2) UEBA : construire les profils + risk_score
    print("[PIPELINE] Building UEBA user profiles...")
    profiles = build_user_profiles(df)
    print(f"[PIPELINE] Built profiles for {len(profiles)} users")

    print("[PIPELINE] Enriching events with risk_score / risk_level...")
    df_enriched = enrich_with_risk(df, profiles)

    # 3) ML : entraîner le modèle + scorer les événements
    print("[PIPELINE] Training ML model (IsolationForest)...")
    train_model(df_enriched)

    print("[PIPELINE] Scoring events with ML anomaly detection...")
    df_ml = score_events(df_enriched)

    # 4) Fusion : calcul de alert_severity + is_alert
    print("[PIPELINE] Computing alert severity...")
    df_ml["alert_severity"] = df_ml.apply(compute_severity, axis=1)
    df_ml["is_alert"] = df_ml["alert_severity"].isin(["medium", "critical"]).astype(int)

    # 5) Préparer les docs pour Elasticsearch
    #    → tous les events enrichis : auth-logs-enriched
    #    → seulement is_alert=1 : alerts-enriched
    docs_enriched = df_ml.to_dict(orient="records")
    docs_alerts = df_ml[df_ml["is_alert"] == 1].to_dict(orient="records")

    print(f"[PIPELINE] Will index {len(docs_enriched)} enriched events into {INDEX_ENRICHED}")
    bulk_index(INDEX_ENRICHED, docs_enriched)

    print(f"[PIPELINE] Will index {len(docs_alerts)} alerts into {INDEX_ALERTS_ENRICHED}")
    bulk_index(INDEX_ALERTS_ENRICHED, docs_alerts)

    print("[PIPELINE] Done. UEBA + ML enrichment pushed to Elasticsearch.")


if __name__ == "__main__":
    run_pipeline_from_elastic()
