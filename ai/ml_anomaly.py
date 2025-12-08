from elasticsearch import Elasticsearch, helpers
from sklearn.ensemble import IsolationForest
import math

# =========================
# CONFIG
# =========================

ES_HOST = "http://localhost:9200"
INDEX = "auth-logs-enriched"   # we will read AND update this index


def get_es_client():
    es = Elasticsearch(ES_HOST)
    if not es.ping():
        raise RuntimeError(f"Cannot connect to Elasticsearch at {ES_HOST}")
    return es


# =========================
# STEP 1 – LOAD ALL DOCS
# =========================

def load_all_events(es):
    all_hits = []

    page = es.search(
        index=INDEX,
        body={"query": {"match_all": {}}},
        size=1000,
        scroll="2m",
    )

    scroll_id = page["_scroll_id"]
    hits = page["hits"]["hits"]
    all_hits.extend(hits)

    while len(hits) > 0:
        page = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = page["_scroll_id"]
        hits = page["hits"]["hits"]
        all_hits.extend(hits)

    print(f"Loaded {len(all_hits)} events from index '{INDEX}'")
    return all_hits


# =========================
# STEP 2 – FEATURE ENGINEERING
# =========================

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

def extract_features(src):
    """
    Build a numeric feature vector from one document.
    Returns a list [hour_sin, hour_cos, is_fail, is_internal, risk_score, weekday_num]
    """

    # hour (0-23)
    hour = src.get("hour")
    try:
        h = int(hour) if hour is not None else 0
    except (ValueError, TypeError):
        h = 0
    h = max(0, min(23, h))  # clamp

    angle = 2 * math.pi * h / 24.0
    hour_sin = math.sin(angle)
    hour_cos = math.cos(angle)

    # status -> is_fail
    status = (src.get("status") or "").upper()
    is_fail = 1 if status == "FAIL" else 0

    # internal IP -> is_internal_ip (0/1)
    is_internal_raw = src.get("is_internal_ip")
    if isinstance(is_internal_raw, bool):
        is_internal = 1 if is_internal_raw else 0
    elif isinstance(is_internal_raw, str):
        is_internal = 1 if is_internal_raw.lower() == "true" else 0
    else:
        # maybe tags contain "internal_ip" ?
        tags = src.get("tags") or []
        if isinstance(tags, list) and "internal_ip" in tags:
            is_internal = 1
        else:
            is_internal = 0

    # UEBA risk_score
    risk_score = src.get("risk_score", 0)
    try:
        risk_score = float(risk_score)
    except (ValueError, TypeError):
        risk_score = 0.0

    # weekday
    weekday_str = src.get("weekday")
    weekday_num = WEEKDAY_MAP.get(weekday_str, 0)

    return [hour_sin, hour_cos, is_fail, is_internal, risk_score, weekday_num]


def build_feature_matrix(hits):
    """
    From all hits, build:
    - X: list of feature vectors
    - meta: list of (doc_id, source)
    """
    X = []
    meta = []

    for h in hits:
        src = h["_source"]
        features = extract_features(src)
        X.append(features)
        meta.append((h["_id"], src))

    print(f"Built feature matrix of shape ({len(X)}, {len(X[0]) if X else 0})")
    return X, meta


# =========================
# STEP 3 – TRAIN ISOLATION FOREST
# =========================

def train_isolation_forest(X):
    """
    Train an IsolationForest on feature matrix X.
    contamination is the proportion of anomalies we *expect* (e.g. 10%).
    """
    if not X:
        raise RuntimeError("No data for training the model (X is empty).")

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,   # assume ~10% anomalies (you can adjust)
        random_state=42,
    )
    model.fit(X)
    return model


def compute_anomaly_scores(model, X):
    """
    Use model to compute anomaly scores and flags.

    - model.decision_function(X): higher is more NORMAL, lower is more ANOMALOUS
    We invert it so that higher score means more anomalous.
    """
    import numpy as np

    decision = model.decision_function(X)   # larger -> more normal
    decision = -decision                    # invert: larger -> more anomalous

    # Normalize to [0, 1]
    d_min = decision.min()
    d_max = decision.max()
    if d_max - d_min > 1e-6:
        scores = (decision - d_min) / (d_max - d_min)
    else:
        scores = np.zeros_like(decision)

    # model.predict: 1 = normal, -1 = anomaly
    preds = model.predict(X)
    is_anomaly = (preds == -1)

    return scores, is_anomaly


# =========================
# STEP 4 – UPDATE DOCS IN ES
# =========================

def update_docs_with_ml(es, meta, scores, flags):
    """
    Use bulk update to add:
    - ml_anomaly_score
    - ml_is_anomaly (bool)
    to each doc.
    """
    actions = []

    for (doc_id, src), score, flag in zip(meta, scores, flags):
        action = {
            "_op_type": "update",
            "_index": INDEX,
            "_id": doc_id,
            "doc": {
                "ml_anomaly_score": float(score),
                "ml_is_anomaly": bool(flag),
            },
        }
        actions.append(action)

    if actions:
        helpers.bulk(es, actions)
        print(f"Updated {len(actions)} documents in '{INDEX}' with ML fields.")
    else:
        print("No documents to update.")


def main():
    es = get_es_client()

    # 1) load docs
    hits = load_all_events(es)
    if not hits:
        print("No events in index, aborting.")
        return

    # 2) build features
    X, meta = build_feature_matrix(hits)

    # 3) train model
    model = train_isolation_forest(X)
    print("IsolationForest model trained.")

    # 4) compute scores
    scores, flags = compute_anomaly_scores(model, X)
    print("Anomaly scores computed.")

    # 5) update docs
    update_docs_with_ml(es, meta, scores, flags)

    print("ML anomaly enrichment done.")


if __name__ == "__main__":
    main()
