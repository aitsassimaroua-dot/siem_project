# ai/ml_anomaly.py

import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

from config import (
    DATA_DIR,
    SAMPLE_LOGS_ENRICHED,
    SAMPLE_LOGS_ENRICHED_ML,
    MODEL_DIR,
    ISOFOREST_MODEL_PATH,
)
from features import build_feature_matrix

def load_enriched_events(path: str = SAMPLE_LOGS_ENRICHED) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def train_model(df: pd.DataFrame):
    X = build_feature_matrix(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=0.01,  # proportion attendue d'anomalies
        random_state=42,
        n_estimators=100,
    )
    model.fit(X_scaled)

    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    joblib.dump((scaler, model), ISOFOREST_MODEL_PATH)
    print(f"[ML] Model saved to {ISOFOREST_MODEL_PATH}")

def score_events(df: pd.DataFrame) -> pd.DataFrame:
    X = build_feature_matrix(df)
    scaler, model = joblib.load(ISOFOREST_MODEL_PATH)
    X_scaled = scaler.transform(X)

    scores = model.decision_function(X_scaled)  # plus petit = plus anormal
    preds = model.predict(X_scaled)  # -1 = anomalie, 1 = normal

    df["ml_anomaly_score"] = -scores  # plus grand = plus anormal
    df["ml_is_anomaly"] = (preds == -1).astype(int)
    return df

def main():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    df = load_enriched_events()
    print(f"[ML] Loaded {len(df)} enriched events")

    # entraînement
    train_model(df)

    # scoring
    df_scored = score_events(df)
    df_scored.to_csv(SAMPLE_LOGS_ENRICHED_ML, index=False)
    print(f"[ML] Saved scored events to {SAMPLE_LOGS_ENRICHED_ML}")

if __name__ == "__main__":
    main()
